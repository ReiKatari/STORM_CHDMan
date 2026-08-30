# src/workers.py
import os
import subprocess
import re

import zipfile
import shutil
import time
from PyQt6.QtCore import QThread, pyqtSignal
from src.logic import calculate_sha1, get_bin_files, get_serial_from_file, get_chd_info, get_platform_from_dats, get_serial_from_filename, get_total_size, get_readable_size, detect_fast_platform, detect_platform_from_serial, extract_archive
from src.config import T, get_app_dir, get_resource_path

class ScanThread(QThread):
    """Scans directories recursively for game files"""
    filesFound = pyqtSignal(list) # Emits list of dicts
    finished = pyqtSignal()

    def __init__(self, paths):
        super().__init__()
        self.paths = paths
        self.extensions = {'.cue', '.gdi', '.iso', '.chd', '.mds', '.nrg', '.ccd', '.img', '.toc', '.zip', '.7z', '.rar'}

    def run(self):
        seen = set()
        batch = []
        
        # Helper to emit and clear batch
        def flush_batch():
            if batch:
                self.filesFound.emit(batch)
                batch.clear()
                time.sleep(0.01) # Small yield to let GUI process

        for path in self.paths:
            if not os.path.exists(path): continue
            
            # Helper to check extension
            def is_valid(p):
                 return os.path.splitext(p)[1].lower() in self.extensions

            # Helper to process file
            def process_file(file_path, is_from_dir=False):
                try:
                    if file_path in seen: return
                    
                    # 1. Display Name
                    if is_from_dir:
                        display_name = os.path.basename(os.path.dirname(file_path))
                    else:
                        display_name = os.path.splitext(os.path.basename(file_path))[0]
                    
                    data = {
                        "path": file_path,
                        "display_name": display_name,
                        "size": -1, # Defer
                        "readable_size": "...",
                        "count": -1, # Defer
                        "format": "...",
                        "is_from_dir": is_from_dir
                    }
                    
                    batch.append(data)
                    seen.add(file_path)
                    
                    if len(batch) >= 10: 
                        flush_batch()
                        
                except:
                    pass

            if os.path.isfile(path):
                if is_valid(path):
                    process_file(path, False)
                    
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        full_path = os.path.join(root, file)
                        if is_valid(full_path):
                            process_file(full_path, True)
                            
        flush_batch() # Emit remaining
        self.finished.emit()

class InfoThread(QThread):
    """Calculates size, bin count, and format in background"""
    # row, size, readable_size, count, format
    infoReady = pyqtSignal(int, int, str, int, str)
    
    # Files/folders to skip (not game images)
    SKIP_PATTERNS = ['storm', 'chdman', 'python', 'setup', 'readme', 'license', 'changelog', '.exe', '.dll', '.py']
    
    def __init__(self, data_list):
        super().__init__()
        self.data_list = data_list # List of (row, path)
        
    def run(self):
        for row, path in self.data_list:
            if not os.path.exists(path): continue
            
            # Skip non-game files
            basename = os.path.basename(path).lower()
            if any(skip in basename for skip in self.SKIP_PATTERNS):
                continue
            
            try:
                ext = os.path.splitext(path)[1].lower()
                
                # Fast size calculation
                if ext in ['.zip', '.7z', '.rar']:
                    # For archives, just use archive size (extraction takes too long)
                    size = os.path.getsize(path)
                    count = 1
                elif ext in ['.cue', '.gdi']:
                    # Parse CUE/GDI for bin count - add +1 for the CUE/GDI file itself
                    bins = get_bin_files(path)
                    count = (len(bins) + 1) if bins else 1  # +1 for CUE/GDI file
                    size = sum(os.path.getsize(b) for b in bins if os.path.exists(b)) if bins else os.path.getsize(path)
                else:
                    size = os.path.getsize(path)
                    count = 1
                
                readable_size = get_readable_size(size)
                
                # Fast format detection
                if ext == '.gdi' or 'dreamcast' in basename:
                    fmt = "CD-ROM"
                elif size < 900 * 1024 * 1024:  # < 900MB
                    fmt = "CD-ROM"
                else:
                    fmt = "DVD-ROM"
                
                self.infoReady.emit(row, size, readable_size, count, fmt)
                
            except Exception as e:
                # Emit default values on error to keep UI responsive
                self.infoReady.emit(row, 0, "N/A", 1, "N/A")

class AnalysisThread(QThread):
    """Calculates SHA1, detects Serial and Platform"""
    # row, pct, status, sha1, serial, platform, path
    progress = pyqtSignal(int, int, str, str, str, str, str) 
    log = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, table_items, lang="EN"):
        super().__init__()
        self.items = table_items
        self.lang = lang
        self.is_running = True
        self.chdman_exe = get_resource_path("chdman.exe")
        self.dats_folder = os.path.join(get_app_dir(), "DATs")

    def stop(self):
        self.is_running = False

    def run(self):
        for item in self.items:
            if not self.is_running: break
            time.sleep(0.005) # Yield to main thread
            
            path = item['path']
            row = item['row']
            
            # Defensive check: File existence
            if not os.path.exists(path):
                self.log.emit(f"Error: File not found {path}")
                self.progress.emit(row, 0, "StatusError", "", "", "", path)
                continue

            ext = os.path.splitext(path)[1].lower()
            
            sha1 = ""
            serial = ""
            platform = ""
            
            self.log.emit(f"{T('LogAnalyzing', self.lang)} {os.path.basename(path)}")
            
            # Check if file is an archive
            is_archive = ext in ['.zip', '.rar', '.7z']
            temp_dir = None
            actual_path = path  # Path to analyze (may change if archive is extracted)
            
            try:
                # --- TRY IN-ARCHIVE SERIAL READING FIRST (ZIP only) ---
                archive_serial = None
                if ext == '.zip':
                    try:
                        from src.logic import get_serial_from_archive
                        self.progress.emit(row, 0, "StatusScanning", "", "", "", path)
                        archive_serial = get_serial_from_archive(path, platform=None)
                        if archive_serial:
                            serial = archive_serial
                            self.log.emit(f"Serial from archive: {serial}")
                    except Exception as e:
                        self.log.emit(f"In-archive scan failed: {e}")
                
                # --- ARCHIVE EXTRACTION FOR ANALYSIS (if needed) ---
                if is_archive and not archive_serial:
                    self.progress.emit(row, 0, "StatusExtracting", "", "", "", path)
                    self.log.emit(f"Extracting archive: {os.path.basename(path)}")
                    temp_dir = os.path.join(get_app_dir(), "temp_analysis", f"tmp_{row}_{int(time.time()*1000)}")
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    if extract_archive(path, temp_dir):
                        # Find main disc image file
                        for root, _, files in os.walk(temp_dir):
                            for f in files:
                                f_ext = os.path.splitext(f)[1].lower()
                                if f_ext in ['.cue', '.gdi', '.iso', '.chd', '.bin', '.img']:
                                    actual_path = os.path.join(root, f)
                                    ext = f_ext
                                    self.log.emit(f"Found: {f}")
                                    break
                            if actual_path != path:
                                break
                    else:
                        self.log.emit("Archive extraction failed")
                
                # Fast Platform Detection
                target_bin = actual_path
                try:
                    if ext == '.cue':
                        c_bins = get_bin_files(actual_path)
                        if c_bins and len(c_bins) > 0 and os.path.exists(c_bins[0]):
                             target_bin = c_bins[0]
                except:
                    pass

                fast_plat = None
                try:
                    if os.path.exists(target_bin):
                        fast_plat = detect_fast_platform(target_bin)
                except: pass

                if fast_plat:
                    platform = fast_plat
                    self.progress.emit(row, 0, "StatusHashing", "", "", platform, path)
                    self.log.emit(f"{T('LogPlatform', self.lang)} {platform} (Fast)")
                
                # Progress Callback
                def update_prog(processed, total):
                    if not self.is_running: return
                    if total > 0:
                        pct = int((processed / total) * 100)
                        if pct % 5 == 0:
                            self.progress.emit(row, pct, "StatusHashing", "", "", platform, path)
                
                if ext == '.chd':
                    self.progress.emit(row, 0, "StatusAnalyzing", "", "", platform, path)
                    try:
                        info = get_chd_info(path, self.chdman_exe)
                        sha1 = info.get('sha1', "")
                        serial = info.get('serial', "")
                    except: pass
                    if not sha1:
                        sha1 = calculate_sha1(path, update_prog)
                else:
                    if not fast_plat: self.progress.emit(row, 0, "StatusHashing", "", "", "", path)
                    sha1 = calculate_sha1(target_bin, update_prog) or ""
                    self.progress.emit(row, 100, "StatusScanning", sha1, "", platform, path)
                    
                    try:
                        scan_target = target_bin
                        if ext == '.cue': 
                            bins = get_bin_files(path)
                            if bins and len(bins) > 0 and os.path.exists(bins[0]):
                                scan_target = bins[0]
                                
                        # SKIP SERIAL SEARCH FOR 3DO
                        is_3do = platform == "Panasonic - 3DO Interactive Multiplayer"
                        
                        if os.path.exists(scan_target) and not is_3do:
                            s = get_serial_from_file(scan_target, platform=platform)
                            if s: 
                                serial = s
                                self.log.emit(f"Serial found: {serial}")
                    except Exception as e:
                        self.log.emit(f"Serial scan error: {e}")
                
                if sha1:
                    self.log.emit(f"{T('LogHashed', self.lang)} {sha1}")
                    
                # NOTE: Disabled filename fallback - it's unreliable and returns wrong serials
                # if not serial:
                #     try:
                #         serial = get_serial_from_filename(os.path.basename(path)) or "" 
                #     except: pass
                
                # Platform Recognition (DATs)
                if sha1 and os.path.exists(self.dats_folder):
                    try:
                        if any(f.endswith('.zip') or f.endswith('.dat') for f in os.listdir(self.dats_folder)):
                            res = get_platform_from_dats(sha1, self.dats_folder)
                            if res:
                                dat_plat, dat_serial = res
                                if dat_plat:
                                    platform = dat_plat
                                    self.log.emit(f"{T('LogPlatform', self.lang)} {platform}")
                                if dat_serial:
                                    serial = dat_serial
                                    self.log.emit(f"Serial from DAT: {serial}")
                    except: pass

                # Fallback: Infer platform from serial if still missing
                if not platform and serial:
                    inferred = detect_platform_from_serial(serial)
                    if inferred:
                        platform = inferred
                        self.log.emit(f"Platform inferred from serial: {platform}")

                # Save to serial cache
                if sha1:
                    try:
                        from src.logic import save_serial_to_cache
                        filename = os.path.basename(path)
                        save_serial_to_cache(filename, sha1, serial, platform)
                    except: pass

                self.progress.emit(row, 100, "StatusReady", sha1, serial, platform, path)
            except Exception as e:
                self.log.emit(f"Analysis Error: {e}")
                self.progress.emit(row, 0, "StatusError", "", "", "", path)
            finally:
                # Cleanup temp directory if created
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        import shutil
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    except: pass
                
        self.finished.emit()

class ConversionThread(QThread):
    progress = pyqtSignal(int, int, str) # row, pct, status
    fileFinished = pyqtSignal(int, object) # row, size (object for >2GB support)
    logOutput = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, items, options):
        super().__init__()
        self.items = items # List of dicts
        self.options = options
        self.is_running = True
        self.chdman_exe = get_resource_path("chdman.exe")

    def stop(self):
        self.is_running = False

    def run(self):
        for item in self.items:
            if not self.is_running: break
            
            row = item['row']
            original_input_path = item['path']
            input_file = original_input_path
            original_display_name = item['display_name']
            
            # Determine Output Path
            platform = item.get('platform', "")
            out_root = self.options['output_folder']
            if not out_root: out_root = os.getcwd()
            
            target_folder = out_root
            
            # Platform Specific Output Folder Override
            platform_folders = self.options.get('platform_output_folders', [])
            override_path = None
            if platform_folders and platform:
                for pf in platform_folders:
                    if pf.get('enabled', False) and pf.get('platform') == platform:
                        custom_path = pf.get('path', "")
                        if custom_path:
                            override_path = custom_path
                            self.logOutput.emit(f"Using Custom Output Folder for {platform}: {override_path}")
                            break
            
            if override_path:
                target_folder = override_path
            elif self.options['recognition'] and platform:
                target_folder = os.path.join(out_root, platform)
            
            # Determine command early for subfolder logic
            ext = os.path.splitext(input_file)[1].lower()
            is_chd = (ext == '.chd')
            is_archive = ext in ['.zip', '.7z', '.rar']
            
            # v1.1.0: Extract to Subfolders
            if is_chd and self.options.get('extract_subfolders', False):
                target_folder = os.path.join(target_folder, original_display_name)
            
            if not os.path.exists(target_folder):
                os.makedirs(target_folder, exist_ok=True)
                
            # Output Filename
            out_file = os.path.join(target_folder, original_display_name + ".chd")
            
            if is_chd:
                # Extract
                fmt = item['format']
                cmd_mode = "extractdvd" if "DVD" in fmt else "extractcd"
                if cmd_mode == "extractcd":
                    out_file = os.path.splitext(out_file)[0] + ".cue"
                else:
                    out_file = os.path.splitext(out_file)[0] + ".iso"
            else:
                # Create
                fmt = item['format']
                cmd_mode = "createdvd" if "DVD" in fmt else "createcd"
            
            # CHECK IF EXISTS (Skip Logic)
            if os.path.exists(out_file) and not self.options['force']:
                self.logOutput.emit(f"Skipping: {original_display_name} (File exists)")
                self.progress.emit(row, 100, "StatusSkipped")
                continue
            
            # --- EXTRACTION LOGIC ---
            temp_dir = None
            try:
                if is_archive:
                    self.progress.emit(row, 0, "StatusExtracting")
                    self.logOutput.emit(f"Extracting: {os.path.basename(original_input_path)}")
                    temp_dir = os.path.join(get_app_dir(), "temp_extract", f"tmp_{int(time.time()*1000)}")
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    if extract_archive(original_input_path, temp_dir):
                        found_path = None
                        # Find main file
                        for root, _, files in os.walk(temp_dir):
                            for f in files:
                                f_ext = os.path.splitext(f)[1].lower()
                                if f_ext in ['.cue', '.gdi', '.iso', '.chd', '.mds', '.nrg', '.ccd', '.img', '.toc']:
                                    found_path = os.path.join(root, f)
                                    break
                            if found_path: break
                        
                        if found_path:
                            input_file = found_path
                            
                            # Re-evaluate Format based on extracted size
                            f_size = get_total_size(found_path)
                            if f_size < 900 * 1024 * 1024:
                                fmt = "CD-ROM"
                            else:
                                fmt = "DVD-ROM"
                            
                            # Update command mode
                            if found_path.lower().endswith('.chd'):
                                is_chd = True
                                cmd_mode = "extractdvd" if "DVD" in fmt else "extractcd"
                                if cmd_mode == "extractcd":
                                    out_file = os.path.splitext(out_file)[0] + ".cue"
                                else:
                                    out_file = os.path.splitext(out_file)[0] + ".iso"
                            else:
                                is_chd = False
                                cmd_mode = "createdvd" if "DVD" in fmt else "createcd"
                                out_file = os.path.join(target_folder, original_display_name + ".chd")
                        else:
                            self.logOutput.emit(f"Error: No valid images found in archive {os.path.basename(original_input_path)}")
                            self.progress.emit(row, 0, "StatusError")
                            continue
                    else:
                        self.logOutput.emit(f"Error: Extraction failed for {os.path.basename(original_input_path)}")
                        self.progress.emit(row, 0, "StatusError")
                        continue

                # Build Args
                cmd = [self.chdman_exe, cmd_mode, "-i", input_file, "-o", out_file]
                
                if not is_chd:
                    # Settings defaults
                    algo = self.options['compression']
                    hs_val = self.options['hunk_dvd'] if "DVD" in fmt else self.options['hunk_cd']
                    
                    # --- PRESET LOGIC ---
                    presets = self.options.get('presets', [])
                    if presets and platform:
                        for p in presets:
                            if p.get('enabled', False) and p.get('system') == platform:
                                p_algo = p.get('compression')
                                p_cd = p.get('hunk_cd')
                                p_dvd = p.get('hunk_dvd')
                                
                                if p_algo: algo = p_algo
                                
                                hs_override = p_dvd if "DVD" in fmt else p_cd
                                if hs_override: hs_val = hs_override
                                
                                self.logOutput.emit(f"Using Preset for {platform}: Algo={algo}, Hunk={hs_val}")
                                break
                    
                    cmd.extend(["-c", algo])
                    cmd.extend(["-hs", str(hs_val)])
                    cmd.extend(["--numprocessors", str(self.options['threads'])])
                
                if self.options['force']: cmd.append("-f")
                
                # Use localized status key "StatusProcessing"
                self.progress.emit(row, 0, "StatusProcessing")
                self.logOutput.emit(f"Processing: {os.path.basename(input_file)}")
                self.logOutput.emit(f"Command: {' '.join(cmd)}")
                
                start_time = time.time()
                
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                while True:
                    if not self.is_running:
                        process.kill()
                        break
                    line = process.stdout.readline()
                    if not line: break
                    
                    txt = line.decode('utf-8', errors='ignore').strip()
                    if txt: self.logOutput.emit(txt)
                    m = re.search(r'(\d+\.?\d*)%', txt)
                    if m:
                        pct = int(float(m.group(1)))
                        self.progress.emit(row, pct, "StatusProcessing")
                
                process.wait()
                duration = time.time() - start_time
                
                if not self.is_running:
                    self.progress.emit(row, 0, "StatusCancelled")
                    self.logOutput.emit("Cancelled by user.")
                elif process.returncode == 0:
                    out_size = 0
                    if os.path.exists(out_file): out_size = os.path.getsize(out_file)
                    self.fileFinished.emit(row, out_size)
                    self.progress.emit(row, 100, "StatusDone")
                    
                    # Log Time
                    lang = self.options.get('language', 'EN')
                    self.logOutput.emit(f"{T('LogTime', lang)} {duration:.2f}s")
                    self.logOutput.emit(f"Done: {os.path.basename(out_file)}\n")
                    
                    # Delete Source if requested
                    if self.options.get('delete_source', False):
                        try:
                            # Delete the ORIGINAL input (archive or source file)
                            if os.path.exists(original_input_path):
                                os.remove(original_input_path)
                                self.logOutput.emit(f"Deleted source: {os.path.basename(original_input_path)}")
                        except Exception as e:
                            self.logOutput.emit(f"Failed to delete source: {e}")
                else:
                    self.progress.emit(row, 0, "StatusError")
                    self.logOutput.emit("chdman error occurred.\n")
            except Exception as e:
                self.logOutput.emit(f"Exception: {e}")
                self.progress.emit(row, 0, "StatusError")
            finally:
                if temp_dir and os.path.exists(temp_dir):
                    # Bypassing bin via shutil.rmtree
                    shutil.rmtree(temp_dir, ignore_errors=True)
        
        self.finished.emit()

class DownloadThread(QThread):
    finished = pyqtSignal(str) 
    progress = pyqtSignal(int, int, str) # count_done, total_count, current_file
    error = pyqtSignal(str)  # New signal for errors
    
    def run(self):
        dats_folder = os.path.join(get_app_dir(), "DATs")
        if not os.path.exists(dats_folder):
            try: os.makedirs(dats_folder)
            except: pass

        from src.logic import DAT_URLS
        import urllib.request
        import zipfile
        import shutil
        import socket
        
    def run(self):
        # Setup Debug Logging
        log_path = os.path.join(get_app_dir(), "debug_download.log")
        def log(msg):
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"{time.strftime('%H:%M:%S')} - {msg}\n")
            except: pass
        
        # Clear old log
        try: open(log_path, "w").close()
        except: pass
        
        log("Worker started.")

        dats_folder = os.path.join(get_app_dir(), "DATs")
        if not os.path.exists(dats_folder):
            try: os.makedirs(dats_folder)
            except: pass
            log(f"Created DATs folder: {dats_folder}")

        try:
            from src.logic import DAT_URLS
            log(f"Imported DAT_URLS: {len(DAT_URLS)} items")
        except Exception as e:
            log(f"Error importing DAT_URLS: {e}")
            self.finished.emit(f"Internal Error: Could not load URL list. {e}")
            return

        import urllib.request
        import zipfile
        import shutil
        import socket
        import ssl
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        
        socket.setdefaulttimeout(30) # 30s timeout
        
        # --- SSL Bypass Context ---
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*'
        }

        total = len(DAT_URLS)
        if total == 0:
            self.finished.emit("Error: URL list is empty!")
            return

        downloaded_files = []
        lock = threading.Lock()
        self.processed_count = 0
        
        # Initial UI Update
        self.progress.emit(0, total, f"Подготовка к скачиванию {total} файлов...")
        
        def download_single(url, index):
            filename = url.rstrip('/').split('/')[-1] + ".zip"
            if not filename or filename == ".zip": 
                filename = f"dat_{index}.zip"
            
            output_path = os.path.join(dats_folder, filename)
            log(f"Start DL: {url} -> {output_path}")
            
            # Retry logic
            attempts = 3
            for attempt in range(attempts):
                try:
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                        with open(output_path, 'wb') as out_file:
                            shutil.copyfileobj(response, out_file)
                    
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        log(f"Success: {filename}")
                        return filename
                    else:
                        log(f"Zero size: {filename}")
                except Exception as e:
                    log(f"Retry {attempt+1} for {url}: {e}")
                    time.sleep(1)
            
            log(f"Failed {url} after {attempts} attempts")
            return None

        # --- PHASE 1: PARALLEL DOWNLOAD ---
        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(download_single, url, i+1): (i, url) for i, url in enumerate(DAT_URLS)}
                
                for future in as_completed(futures):
                    idx, url = futures[future]
                    fname = future.result()
                    
                    with lock:
                        self.processed_count += 1
                        current = self.processed_count
                    
                    if fname:
                        downloaded_files.append(fname)
                        msg = f"Скачивание: {current}/{total} - {fname}"
                    else:
                        msg = f"Ошибка: {url}"
                    
                    self.progress.emit(current, total, msg)
        except Exception as e:
            log(f"Executor crash: {e}")
            self.finished.emit(f"Critical DL Error: {e}")
            return

        if not downloaded_files:
            log("No files downloaded.")
            self.finished.emit("Ошибка: Не удалось скачать ни одного файла. См. debug_download.log")
            return

        # --- PHASE 2: EXTRACT ALL ---
        downloaded_files.sort()
        count_ext = 0
        total_ext = len(downloaded_files)
        log(f"Starting extraction of {total_ext} files")
        
        for fname in downloaded_files:
            count_ext += 1
            zip_path = os.path.join(dats_folder, fname)
            
            msg = f"Распаковка: {count_ext}/{total_ext} - {fname}"
            self.progress.emit(count_ext, total_ext, msg)
            
            try:
                if os.path.exists(zip_path):
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(dats_folder)
            except Exception as e:
                log(f"Extract Fail {fname}: {e}")
            
            time.sleep(0.01)

        # --- PHASE 3: DELETE ALL ---
        count_del = 0
        log("Deleting archives")
        for fname in downloaded_files:
            count_del += 1
            zip_path = os.path.join(dats_folder, fname)
            
            msg = f"Удаление: {count_del}/{total_ext} - {fname}"
            self.progress.emit(count_del, total_ext, msg)
            
            try:
                if os.path.exists(zip_path):
                    os.remove(zip_path)
            except: pass
            
            time.sleep(0.01)

        self.finished.emit("DAT-файлы успешно обновлены")
        log("Workflow finished.")



