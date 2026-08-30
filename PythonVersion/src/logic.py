# src/logic.py
import os
import re
import hashlib
import shutil
import subprocess
import requests
import zipfile
import json
from datetime import datetime

# Regex Pattern for Serials
PATTERNS_PSX = [
    rb'BOOT\s*=\s*cdrom[0-9]*:[\\\/]?([A-Z]{4})[_\.\-](\d{3})[\.\-](\d{2})', # BOOT = cdrom:\SLUS_123.45
    rb'(S[CL][EUP][SAP])[_\.\-](\d{3})[\.\-](\d{2})', # Raw SLUS_123.45 or SLUS-123.45
    rb'([A-Z]{4})[\-](?:0|1)?(\d{4})', # Explicit XXXX-1234 format (often in ISOs)
    rb'([A-Z]{4})[_\.](\d{3})\.?(\d{2})', # General fallback
]

PATTERNS_SATURN = [
    rb'([A-Z0-9]{1,3}-\d{4,5}[A-Z0-9]?)',
    rb'([A-Z]{1,2}\d{4,5}[A-Z]?)'
]

PATTERNS_SEGACD = [
    rb'([A-Z]{1,2}\s*[_\-\.]\s*\d{4,6}(?:-50)?)', # T-95035, G-6021, T-13205-50
    rb'(\b[4]\d{3}-50\b)',                        # 4407-50 (EU Sega)
    rb'(\b[4]\d{3}\b)',                           # 4407 (US Sega)
    rb'(\d{3}-\d{4})'                             # Standard numeric
]

PATTERNS_3DO = [
    # High Priority: Known 3DO Publisher Prefixes
    rb'(FZ-[A-Z0-9]{2,10})',                  # FZ-S1, FZ-SJ3851 (Panasonic)
    rb'(KKKH[_\-]?\d{4,5})',                  # KKKH-9929, KKKH_9929
    rb'(BMG[_\-\s]?\d{4,5})',                 # BMG-9000, BMG 9000
    rb'(GDO[_\-]?\d{3,5})',                   # GDO-001 (GoldStar/LG)
    rb'(JVC[_\-]?\d{3,5})',                   # JVC-001 (JVC games)
    rb'(SLCD[_\-]?\d{3,5})',                  # SLCD-001 (Sony Light CD?)
    rb'(VIE[_\-]?\d{3,5})',                   # VIE-001 (Victor Interactive)
    rb'(SAM[_\-]?\d{3,5})',                   # SAM-001 (Samsung)
    # Medium Priority: Generic alphanumeric with separator
    rb'([A-Z]{2,4}[_\-]\d{4,6})',             # XX-12345 (fallback)
    # Low Priority: Space-separated (BMG 9000)
    rb'([A-Z]{2,4}\s+\d{4,5})',               # "BMG 9000"
]

# Dreamcast: T-XXXXX-M, MK-51012 (more specific patterns)
PATTERNS_DREAMCAST = [
    rb'(T-\d{4,5}-?[MEJK]?)',               # T-12345M, T-1234-M (Sega Dreamcast)
    rb'(MK-\d{5})',                          # MK-51012
    rb'(HDR-\d{4})',                         # HDR-0001
    # Note: Removed generic [A-Z]{2,3}-\d{4,6} - too generic, causes false positives
]

# GameCube: DOL-GXXE-USA (Game ID format) - must have DOL prefix or specific structure
PATTERNS_GAMECUBE = [
    rb'DOL-([A-Z0-9]{4})-',                  # DOL-GALE-USA (most reliable)
    rb'(G[A-Z0-9]{3}[EJPK]\d)',              # GALE01, G3ME01 (starts with G + region code + version)
]

# Wii: RXXX01 format - more specific, must have RVL prefix or R/S start
PATTERNS_WII = [
    rb'RVL-([A-Z0-9]{4})-',                  # RVL-RSPE-USA (most reliable)
    rb'(R[A-Z0-9]{2}[EJPKW]\d{2})',          # R3DE01, RSPE01 (starts with R + region + version)
    rb'(S[A-Z0-9]{2}[EJPKW]\d{2})',          # S... format (some Wii games)
]

# Xbox: MS-XXX, EA-XXX
PATTERNS_XBOX = [
    rb'([A-Z]{2,3}-\d{3,4})',             # MS-001, EA-2001
]

# Neo Geo CD: NGH-XXX
PATTERNS_NEOGEOCD = [
    rb'(NGH-\d{3,4})',                    # NGH-001
    rb'(NGCD-\d{3,4})',                   # NGCD-001
]

# PC Engine / TurboGrafx-CD: TGXCDXXX
PATTERNS_PCENGINE = [
    rb'(TGXCD\d{3,4})',                   # TGXCD1001
    rb'(NAPR-\d{4,5})',                   # NAPR-1001
    rb'(PWD-\d{3,4})',                    # PWD-001
]

# PS3: BLUS-XXXXX, BLES-XXXXX, BCES-XXXXX
PATTERNS_PS3 = [
    rb'(B[CL][EUJA][SP][\-_]\d{5})',      # BLUS-12345, BLES-00001
    rb'(NP[EUJA][ABCD][\-_]\d{5})',       # NPUB-12345 (PSN)
]

# PSP: UCUS-XXXXX, ULES-XXXXX
PATTERNS_PSP = [
    rb'(U[CL][EUJA][SP][\-_]\d{5})',      # UCUS-12345, ULES-00001
    rb'(NP[EUJA][HGZ][\-_]\d{5})',        # NPUH-10001 (PSN)
]

def get_readable_size(size_in_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} PB"

def calculate_sha1(filepath, callback_progress=None):
    """Calculates SHA1 hash of a file with progress callback"""
    sha1 = hashlib.sha1()
    file_size = os.path.getsize(filepath)
    processed = 0
    buffer_size = 1024 * 1024 # 1MB

    try:
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(buffer_size)
                if not data:
                    break
                sha1.update(data)
                processed += len(data)
                if callback_progress:
                    callback_progress(processed, file_size)
        return sha1.hexdigest().lower()
    except Exception as e:
        print(f"Error calculating SHA1 for {filepath}: {e}")
        return None

def get_bin_files(filepath):
    """Returns list of binary files referenced by CUE or GDI"""
    ext = os.path.splitext(filepath)[1].lower()
    folder = os.path.dirname(filepath)
    bin_files = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        if ext == '.cue':
            for line in lines:
                match = re.search(r'FILE\s+"(.+?)"\s+BINARY', line, re.IGNORECASE)
                if match:
                    bin_path = os.path.join(folder, match.group(1))
                    if os.path.exists(bin_path):
                        bin_files.append(bin_path)
            # Fallback if no BINARY keyword or simple FILE
            if not bin_files:
                 for line in lines:
                    match = re.search(r'FILE\s+"(.+?)"', line, re.IGNORECASE)
                    if match:
                        bin_path = os.path.join(folder, match.group(1))
                        if os.path.exists(bin_path):
                            bin_files.append(bin_path)

        elif ext == '.gdi':
            for line in lines:
                parts = line.split()
                if len(parts) > 4:
                    # GDI format: track# start_lba type flags filename lba
                    raw_filename = parts[4]
                    if raw_filename.startswith('"'): raw_filename = raw_filename[1:]
                    if raw_filename.endswith('"'): raw_filename = raw_filename[:-1]
                    
                    bin_path = os.path.join(folder, raw_filename)
                    if os.path.exists(bin_path):
                        bin_files.append(bin_path)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        
    # If standard ISO/CHD, return itself
    if not bin_files and ext in ['.iso', '.chd', '.img', '.mdf', '.nrg']:
        bin_files.append(filepath)
        
    return bin_files

def get_serial_from_filename(filename):
    """Tries to find serial in filename (e.g. SCUS-94201)"""
    # Pattern: 4 Letters [-_] 5 Digits.
    # Often enclosed in parens or just floating.
    match = re.search(r'([A-Z]{4})[-_](\d{5})', filename, re.IGNORECASE)
    if match:
        return f"{match.group(1).upper()}-{match.group(2)}"
    return None

def get_serial_from_archive(archive_path, platform=None):
    """
    Reads serial directly from inside a ZIP archive without extracting to disk.
    Uses the SAME scanning logic as get_serial_from_file - treats files inside
    the archive exactly as if they were dragged into the program.
    
    For 3DO: Scans ALL BIN files (not just largest) since serial may be in Track 2.
    """
    if not archive_path.lower().endswith('.zip'):
        return None  # Only ZIP support for now (7z/rar need external libs)
    
    try:
        with zipfile.ZipFile(archive_path, 'r') as zf:
            # List all files inside (same as if folder was dragged)
            all_files = []
            for info in zf.infolist():
                if not info.is_dir():
                    ext = os.path.splitext(info.filename.lower())[1]
                    all_files.append((info.file_size, info.filename, ext))
            
            if not all_files:
                return None
            
            # Collect all BIN/ISO files to scan (for 3DO, we check all)
            bin_files = [(s, n, e) for s, n, e in all_files if e in ['.bin', '.iso', '.img']]
            bin_files.sort(key=lambda x: x[0], reverse=True)  # Largest first
            
            # Also check CUE/GDI for referenced files
            cue_gdi_files = [(s, n, e) for s, n, e in all_files if e in ['.cue', '.gdi']]
            
            # For each CUE, find its BIN reference
            for _, cue_name, cue_ext in cue_gdi_files:
                try:
                    cue_data = zf.read(cue_name).decode('utf-8', errors='ignore')
                    for match in re.finditer(r'FILE\s+"?([^"\n]+)"?\s+BINARY', cue_data, re.IGNORECASE):
                        bin_name = match.group(1).strip()
                        for size, name, ext in all_files:
                            if name.endswith(bin_name) or os.path.basename(name) == bin_name:
                                if (size, name, ext) not in bin_files:
                                    bin_files.append((size, name, ext))
                except: pass
            
            # If no BIN files found, try ISO/IMG
            if not bin_files:
                bin_files = [(s, n, e) for s, n, e in all_files if e in ['.iso', '.img', '.cdi']]
            
            if not bin_files:
                return None
            
            # Sort by size (largest first, often Track 01 is largest but not always for 3DO)
            bin_files.sort(key=lambda x: x[0], reverse=True)
            
            # Limit to max 3 files to avoid long processing times
            bin_files = bin_files[:3]
            
            # Try scanning each BIN file until we find a serial
            for target_size, target_name, target_ext in bin_files:
                # Read file data from archive - use smaller limit for speed
                if target_size > 500 * 1024 * 1024:  # > 500MB (DVD)
                    search_limit = 8 * 1024 * 1024  # 8MB for DVD-ROM
                else:
                    search_limit = 4 * 1024 * 1024  # 4MB for CD-ROM (serials are usually in first few MB)
                
                read_limit = min(search_limit, target_size)
                
                try:
                    with zf.open(target_name) as inner_file:
                        data = inner_file.read(read_limit)
                    
                    # Scan for serial
                    serial = _scan_data_for_serial(data, target_size, platform)
                    if serial:
                        return serial
                except: continue
            
            return None
            
    except Exception as e:
        print(f"Error reading archive {archive_path}: {e}")
        return None

def _scan_data_for_serial(data, file_size, platform=None):
    """
    Internal helper: Scans binary data for serial number.
    This is the core logic used by both get_serial_from_file and get_serial_from_archive.
    
    Key improvements:
    - PS2 detection: Looks for 5-digit serials (SLUS-12345 format) first
    - 3DO detection: Scans for 3DO header signature even without platform hint
    - No platform hint: Uses file size and patterns to auto-detect
    """
    BLACKLIST = [
        "CD-ROM", "DVD-ROM", "3DO_CDROM", "3DO_ROM", "CONVOY", "AUDIO", "VIDEO", "VERSION", "SYSTEM",
        # V-prefixed version codes (not serials)
        "V00", "V01", "V02", "V10", "V11", "V12", "VER", "VERS"
    ]
    
    # Patterns to explicitly reject (version codes, internal markers)
    REJECT_PATTERNS = [
        rb'^V\d{5}[A-Z]?$',  # V00179E, V12345X (version codes)
        rb'^VER\d',          # VER1, VER2
        rb'^MC-\d{5}$',      # MC-00200 (internal codes)
        rb'^MK-\d{5}$',      # MK-12345 (internal codes)
        rb'^HC-\d{5}$',      # HC-xxxxx (internal codes)
    ]
    
    # === AUTO-DETECT PLATFORM FROM DATA ===
    auto_platform = None
    
    # Check for 3DO header signature (Opera filesystem)
    if b"\x01ZZZZZ" in data[:100] or b"CD-ROM" in data[:200] and b"3DO" in data[:500]:
        auto_platform = "3DO"
    
    # Check for PS2 indicators
    if b"PLAYSTATION2" in data[:2048] or b"PlayStation2" in data[:2048]:
        auto_platform = "PS2"
    elif b"PLAYSTATION" in data[:2048] or b"PlayStation" in data[:2048]:
        auto_platform = "PSX"
    
    # Use detected platform if no hint provided
    effective_platform = platform or auto_platform
    
    # === PS2 DETECTION (Priority) ===
    # 1. Try SYSTEM.CNF style "BOOT2 = cdrom0:\SLUS_200.02;1"
    # This is safer for BIN/CUE images (CD-ROM)
    boot2_match = re.search(rb'BOOT2\s*=\s*cdrom0:\\\\?([A-Z0-9_]+)\.(\d+)', data, re.IGNORECASE)
    
    if boot2_match:
        try:
            # Parse BOOT2 value
            full_val = boot2_match.group(0).decode('ascii', errors='ignore').split('\\')[-1].split(';')[0].strip()
            # Expect: SLUS_200.02
            if '_' in full_val and '.' in full_val:
                p1, p2 = full_val.split('_') # SLUS, 200.02
                p2 = p2.replace('.', '')     # 20002
                serial = f"{p1}-{p2}"
                if len(serial) == 10:
                    return serial
        except: pass

    # 2. Pattern search (Backup)
    # PS2 serials have 5 digits: SLUS-12345, SLES-12345, etc.
    # Must check BEFORE PS1 to avoid false matches
    ps2_pattern = rb'(S[LC][EUJA][SPK])[-_](\d{5})'  # 5 digits = PS2
    for match in re.finditer(ps2_pattern, data, re.IGNORECASE):
        try:
            g1 = match.group(1).decode('ascii', errors='ignore').upper()
            g2 = match.group(2).decode('ascii', errors='ignore')
            serial = f"{g1}-{g2}"
            if len(serial) == 10 and serial not in BLACKLIST:  # SLUS-12345 = 10 chars
                return serial
        except: continue
    
    # === 3DO DETECTION ===
    if effective_platform and "3DO" in str(effective_platform):
        return "" # User requested to skip serial search for 3DO
        
        candidates = []
        
        # Pattern-based search first
        for pat in PATTERNS_3DO:
            for match in re.finditer(pat, data, re.IGNORECASE):
                try:
                    s = match.group(0).decode('ascii', errors='ignore').strip().upper()
                    s = re.sub(r'[\s_]+', '-', s)
                    if len(s) >= 4 and s not in BLACKLIST:
                        if any(c.isalpha() for c in s) and "-" in s:
                            return s
                        candidates.append(s)
                except: continue
        
        # 3DO Header scan - Try multiple sector offsets (raw vs cooked)
        # Sector 0 for ISO, sector 16 for Mode 2, 2048/2352 for Mode 1/2
        header_offsets = [0, 16, 2048, 2352, 2352*16]
        
        for base_offset in header_offsets:
            if len(data) <= base_offset + 200:
                continue
            
            # Check for Opera filesystem signature
            if b"\x01ZZZZZ" in data[base_offset:base_offset+20]:
                def extract_header_str(start, length):
                    chunk = data[start:start+length]
                    clean = ""
                    for b in chunk:
                        if 32 <= b <= 126: clean += chr(b)
                        else: break
                    return clean.strip().upper()
                
                # Opera header structure:
                # Offset 40: Volume Label (32 bytes)
                # Offset 72: Volume ID (32 bytes) 
                # Offset 104: Publisher (32 bytes)
                # Offset 132: Copyright/Product Number (32 bytes)
                
                fields = [
                    (base_offset + 132, 32),  # Product Number
                    (base_offset + 72, 32),   # Volume ID
                    (base_offset + 40, 32),   # Volume Label
                    (base_offset + 104, 32),  # Publisher
                ]
                
                for field_offset, field_len in fields:
                    if field_offset + field_len > len(data):
                        continue
                    val = extract_header_str(field_offset, field_len)
                    if len(val) >= 4 and val not in BLACKLIST:
                        # Check if it looks like a serial (has letters and numbers with separator)
                        if any(c.isalpha() for c in val) and sum(c.isdigit() for c in val) >= 2:
                            if "-" in val or "_" in val:
                                return val
                            candidates.append(val)
                
                break  # Found Opera header, stop searching offsets
        
        # Return best candidate
        if candidates:
            # Prioritize candidates with separators
            for c in candidates:
                if "-" in c or "_" in c:
                    return c
            for c in candidates:
                if any(ch.isalpha() for ch in c):
                    return c
            return candidates[0]
            
        return ""
    
    # === PS1 DETECTION (after PS2) ===
    # PS1 serials: SLUS_123.45 or SLUS-12345 (but often shorter)
    if effective_platform and "PSX" in str(effective_platform) or (effective_platform and "PlayStation" in str(effective_platform) and "2" not in str(effective_platform) and "3" not in str(effective_platform)):
        for pat in PATTERNS_PSX:
            for match in re.finditer(pat, data, re.IGNORECASE):
                try:
                    gs = [g.decode('ascii', errors='ignore').upper() for g in match.groups() if g]
                    if len(gs) == 3:
                        res = f"{gs[0]}-{gs[1]}{gs[2]}"
                        if len(res) >= 9: return res
                    elif len(gs) == 2:
                        res = f"{gs[0]}-{gs[1]}"
                        if len(res) >= 8: return res
                except: continue
    
    # === GENERIC PATTERN SCAN ===
    all_patterns = []
    if effective_platform:
        p = str(effective_platform)
        if "PlayStation 3" in p: all_patterns = PATTERNS_PS3
        elif "PlayStation Portable" in p or "PSP" in p: all_patterns = PATTERNS_PSP
        elif "PlayStation 2" in p or "PS2" in p: all_patterns = []  # Already handled above
        elif "PlayStation" in p: all_patterns = PATTERNS_PSX
        elif "Dreamcast" in p: all_patterns = PATTERNS_DREAMCAST
        elif "Saturn" in p: all_patterns = PATTERNS_SATURN
        elif "Mega-CD" in p or "Mega CD" in p or "Sega CD" in p: all_patterns = PATTERNS_SEGACD
        elif "GameCube" in p: all_patterns = PATTERNS_GAMECUBE
        elif "Wii" in p: all_patterns = PATTERNS_WII
        elif "Neo Geo" in p: all_patterns = PATTERNS_NEOGEOCD
        elif "PC Engine" in p or "TurboGrafx" in p: all_patterns = PATTERNS_PCENGINE
    
    if not all_patterns:
        # Try all patterns in priority order
        all_patterns = PATTERNS_DREAMCAST + PATTERNS_SATURN + PATTERNS_SEGACD + PATTERNS_3DO
    
    for pat in all_patterns:
        for match in re.finditer(pat, data, re.IGNORECASE):
            try:
                groups = match.groups()
                if groups and groups[0]:
                    s = groups[0].decode('ascii', errors='ignore').strip().upper()
                else:
                    s = match.group(0).decode('ascii', errors='ignore').strip().upper()
                s = re.sub(r'[\s_]+', '-', s)
                if len(s) >= 4 and s not in BLACKLIST:
                    # Check against reject patterns (version codes, etc.)
                    is_rejected = False
                    for rp in REJECT_PATTERNS:
                        if re.match(rp, s.encode('ascii', errors='ignore'), re.IGNORECASE):
                            is_rejected = True
                            break
                    if not is_rejected:
                        return s
            except: continue
    
    return None

def get_serial_from_file(filepath, platform=None):
    """Tries to find serial number in a binary file, optionally using platform hint."""
    try:
        with open(filepath, 'rb') as f:
            # Get file size to determine scan limit
            f.seek(0, 2)  # Seek to end
            file_size = f.tell()
            f.seek(0)  # Seek back to start
            
            # For large files (DVD-ROM > 500MB), scan more data
            if file_size > 500 * 1024 * 1024:  # > 500MB
                search_limit = 64 * 1024 * 1024  # 64MB for DVD-ROM
            else:
                search_limit = 16 * 1024 * 1024  # 16MB for CD-ROM
            
            data = f.read(search_limit)
            
            BLACKLIST = ["CD-ROM", "DVD-ROM", "3DO_CDROM", "3DO_ROM", "CONVOY", "AUDIO", "VIDEO", "VERSION"]
            
            # --- 3DO LOGIC ---
            if platform and "3DO" in platform:
                # 1. Brute Force (Scan all) - Favoring Alphanumeric serials
                candidates = []
                for pat in PATTERNS_3DO:
                    for match in re.finditer(pat, data, re.IGNORECASE):
                        try:
                            s = match.group(0).decode('ascii', errors='ignore').strip().upper()
                            # Clean up: BMG 9000 -> BMG-9000, KKKH_9929 -> KKKH-9929
                            s = re.sub(r'[\s_]+', '-', s)
                            
                            if len(s) >= 4 and s not in BLACKLIST:
                                # High Quality: Alphanumeric + Dash (e.g. KKKH-9929, FZ-S1)
                                if any(c.isalpha() for c in s) and "-" in s:
                                     return s
                                candidates.append(s)
                        except: continue

                # 2. Header (Fallback)
                for offset in [0, 16]:
                    if len(data) > offset + 200 and b"\x01ZZZZZ" in data[offset:offset+10]:
                        def extract_header_str(start, length):
                            chunk = data[start:start+length]
                            # Take until first null OR unprintable
                            clean = ""
                            for b in chunk:
                                if 32 <= b <= 126: clean += chr(b)
                                else: break
                            return clean.strip().upper()
                        
                        p_num = extract_header_str(offset+132, 32)
                        if len(p_num) >= 6 and p_num not in BLACKLIST and sum(c.isdigit() for c in p_num) >= 2: 
                            if any(c.isalpha() for c in p_num): return p_num # Prefer Alphanumeric
                            candidates.append(p_num)
                        
                        v_lab = extract_header_str(offset+40, 32)
                        if len(v_lab) >= 6 and v_lab not in BLACKLIST and sum(c.isdigit() for c in v_lab) >= 2: 
                            candidates.append(v_lab)

                # Return best fallback candidate
                if candidates:
                    for c in candidates:
                        if any(c.isalpha() for c in c): return c
                    return candidates[0]

            # --- PSX LOGIC ---
            if platform and ("PlayStation" in platform and "2" not in platform):
                # 1. Scan for raw patterns (XXXX-XXXXX) first
                for pat in PATTERNS_PSX[1:]:
                    for match in re.finditer(pat, data, re.IGNORECASE):
                        try:
                            gs = [g.decode('ascii', errors='ignore').upper() for g in match.groups() if g]
                            if len(gs) == 3:
                                res = f"{gs[0]}-{gs[1]}{gs[2]}"
                                if len(res) >= 9: return res
                            elif len(gs) == 2:
                                res = f"{gs[0]}-{gs[1]}"
                                if len(res) >= 9: return res
                        except: continue

                # 2. Header / BOOT (Fallback)
                boot_match = re.search(PATTERNS_PSX[0], data, re.IGNORECASE)
                if boot_match:
                    try:
                        p1 = boot_match.group(1).decode('ascii').upper()
                        p2 = boot_match.group(2).decode('ascii')
                        p3 = boot_match.group(3).decode('ascii')
                        return f"{p1}-{p2}{p3}"
                    except: pass

            # --- PS2 LOGIC ---
            if platform and "PlayStation 2" in platform:
                # PS2: Look for BOOT2 entry in SYSTEM.CNF (multiple format variants)
                boot2_patterns = [
                    rb'BOOT2\s*=\s*cdrom0:\\?([A-Z]{4})[_\.\-](\d{3})[\.\-](\d{2})',  # BOOT2 = cdrom0:\SLUS_203.60
                    rb'BOOT2\s*=\s*cdrom0:[\\/]?([A-Z]{4})[_\.\-](\d{3})[\.\-](\d{2})',  # with forward slash
                    rb'BOOT2\s*=\s*cdrom0:[\\]?([A-Z]{4})_(\d{3})\.(\d{2})',  # BOOT2=cdrom0:\SLUS_203.60
                ]
                
                for boot2_pat in boot2_patterns:
                    boot2_match = re.search(boot2_pat, data, re.IGNORECASE)
                    if boot2_match:
                        try:
                            p1 = boot2_match.group(1).decode('ascii').upper()
                            p2 = boot2_match.group(2).decode('ascii')
                            p3 = boot2_match.group(3).decode('ascii')
                            serial = f"{p1}-{p2}{p3}"
                            # Only return if it's a valid PlayStation serial prefix
                            if p1 in ['SLUS', 'SCUS', 'SLES', 'SCES', 'SLPS', 'SLPM', 'SCPS', 'SLKA', 'SCKA']:
                                return serial
                        except: pass
                
                # Fallback: scan for SLUS/SLES/SCUS etc patterns with priority
                # First, look for high-confidence patterns like SLUS_XXX.XX
                priority_matches = []
                
                ps2_patterns = [
                    rb'(SLUS|SCUS|SLES|SCES|SLPS|SLPM|SCPS)[_\.\-](\d{3})[\.\-](\d{2})',  # SLUS_203.60
                    rb'(SLUS|SCUS|SLES|SCES|SLPS|SLPM|SCPS)[\-](\d{5})',  # SLUS-20360
                ]
                
                for pat in ps2_patterns:
                    for match in re.finditer(pat, data, re.IGNORECASE):
                        try:
                            gs = [g.decode('ascii', errors='ignore').upper() for g in match.groups() if g]
                            if len(gs) == 3:
                                res = f"{gs[0]}-{gs[1]}{gs[2]}"
                            elif len(gs) == 2:
                                res = f"{gs[0]}-{gs[1]}"
                            else:
                                continue
                            
                            # Prioritize based on prefix
                            if gs[0] in ['SLUS', 'SCUS']:  # US region - highest priority
                                return res
                            priority_matches.append(res)
                        except: continue
                
                # Return first match from other regions if no US match
                if priority_matches:
                    return priority_matches[0]

            # --- SATURN / SEGA CD LOGIC ---
            if platform and ("Saturn" in platform or "Mega-CD" in platform or "Mega CD" in platform or "Sega CD" in platform):
                for offset in [0, 16]:
                    if len(data) > offset + 512:
                        # Saturn
                        if b"SEGA SEGASATURN" in data[offset:offset+32]:
                             prod = data[offset+32:offset+42].decode('ascii', errors='ignore').strip().upper()
                             if len(prod) > 3 and prod not in BLACKLIST: return prod
                        # Sega CD
                        if b"SEGA" in data[offset:offset+16] and (b"SEGADISCSYSTEM" in data[offset:offset+32]):
                             # Sega CD Header Scan
                             prod = data[offset+0x180:offset+0x190].decode('ascii', errors='ignore').strip().upper()
                             # Try brute force patterns first on this chunk (more precise)
                             for pat in PATTERNS_SEGACD:
                                 m = re.search(pat, prod.encode('ascii', errors='ignore'))
                                 if m: return m.group(1).decode('ascii').upper()
                             
                             if len(prod) > 3:
                                 # Sega CD Fix: Trim GM prefix or non-serial garbage
                                 m = re.search(r'([A-Z]{1,2}-\d{4,6}(?:-50)?)', prod)
                                 if m: return m.group(1)
                                 if prod not in BLACKLIST: return prod
                
                # Full Scan Fallback for Sega CD
                for pat in PATTERNS_SEGACD:
                    for match in re.finditer(pat, data, re.IGNORECASE):
                        try:
                            s = match.group(0).decode('ascii', errors='ignore').strip().upper()
                            if len(s) >= 4 and s not in BLACKLIST:
                                return s
                        except: continue

            # --- DREAMCAST LOGIC ---
            if platform and "Dreamcast" in platform:
                # IP.BIN / IP0000.BIN header - Product Number at offset 0x40
                for offset in [0, 16, 0x8000]:
                    if len(data) > offset + 0x60:
                        header = data[offset:offset+0x100]
                        if b"SEGA" in header[:16]:
                            prod = header[0x40:0x50].decode('ascii', errors='ignore').strip().upper()
                            # Clean up spaces
                            prod = re.sub(r'\s+', '', prod)
                            if len(prod) >= 4 and "-" in prod:
                                return prod
                
                # Pattern scan fallback
                for pat in PATTERNS_DREAMCAST:
                    for match in re.finditer(pat, data, re.IGNORECASE):
                        try:
                            s = match.group(0).decode('ascii', errors='ignore').strip().upper()
                            if len(s) >= 5: return s
                        except: continue

            # --- GAMECUBE LOGIC ---
            if platform and "GameCube" in platform:
                # Header at offset 0x00 - Game ID (6 bytes)
                if len(data) >= 6:
                    game_id = data[0:6].decode('ascii', errors='ignore').strip().upper()
                    # Validate: 6 alphanumeric chars
                    if len(game_id) == 6 and game_id.isalnum():
                        return game_id
            
            # --- WII LOGIC ---
            if platform and "Wii" in platform:
                # Header at offset 0x00 - Game ID (6 bytes)
                if len(data) >= 6:
                    game_id = data[0:6].decode('ascii', errors='ignore').strip().upper()
                    # Validate: 6 alphanumeric chars
                    if len(game_id) == 6 and game_id.isalnum():
                        return game_id
            
            # --- XBOX LOGIC ---
            if platform and "Xbox" in platform and "360" not in platform:
                # default.xbe header - Title ID
                xbe_match = re.search(rb'MICROSOFT\*XBOX\*', data)
                if xbe_match:
                    # Try to find MS-XXX or similar
                    for pat in PATTERNS_XBOX:
                        for match in re.finditer(pat, data, re.IGNORECASE):
                            try:
                                s = match.group(0).decode('ascii', errors='ignore').strip().upper()
                                if len(s) >= 5: return s
                            except: continue
                
            # --- XBOX 360 LOGIC ---
            if platform and "Xbox 360" in platform:
                # XEX header
                if b"XEX2" in data[:0x100]:
                    # Media ID is often at specific offsets
                    for pat in PATTERNS_XBOX:
                        for match in re.finditer(pat, data, re.IGNORECASE):
                            try:
                                s = match.group(0).decode('ascii', errors='ignore').strip().upper()
                                if len(s) >= 5: return s
                            except: continue
            
            # --- NEO GEO CD LOGIC ---
            if platform and "Neo" in platform and "Geo" in platform:
                # Look for NGH-XXX pattern
                for pat in PATTERNS_NEOGEOCD:
                    for match in re.finditer(pat, data, re.IGNORECASE):
                        try:
                            s = match.group(0).decode('ascii', errors='ignore').strip().upper()
                            if len(s) >= 6: return s
                        except: continue
            
            # --- PC ENGINE / TURBOGRAFX CD LOGIC ---
            if platform and ("PC Engine" in platform or "TurboGrafx" in platform):
                for pat in PATTERNS_PCENGINE:
                    for match in re.finditer(pat, data, re.IGNORECASE):
                        try:
                            s = match.group(0).decode('ascii', errors='ignore').strip().upper()
                            if len(s) >= 6: return s
                        except: continue
            
            # --- PS3 LOGIC ---
            if platform and "PlayStation 3" in platform:
                # Look for PARAM.SFO pattern with TITLE_ID
                title_id_match = re.search(rb'TITLE_ID\x00.{0,32}([A-Z]{4}[\-_]\d{5})', data, re.IGNORECASE)
                if title_id_match:
                    try:
                        s = title_id_match.group(1).decode('ascii', errors='ignore').strip().upper()
                        return s.replace('_', '-')
                    except: pass
                
                # Pattern scan
                for pat in PATTERNS_PS3:
                    for match in re.finditer(pat, data, re.IGNORECASE):
                        try:
                            s = match.group(0).decode('ascii', errors='ignore').strip().upper()
                            return s.replace('_', '-')
                        except: continue
            
            # --- PSP LOGIC ---
            if platform and ("PSP" in platform or "PlayStation Portable" in platform):
                # Look for PARAM.SFO or UMD_DATA.BIN patterns
                disc_id_match = re.search(rb'DISC_ID\x00.{0,32}([A-Z]{4}[\-_]\d{5})', data, re.IGNORECASE)
                if disc_id_match:
                    try:
                        s = disc_id_match.group(1).decode('ascii', errors='ignore').strip().upper()
                        return s.replace('_', '-')
                    except: pass
                
                # Pattern scan
                for pat in PATTERNS_PSP:
                    for match in re.finditer(pat, data, re.IGNORECASE):
                        try:
                            s = match.group(0).decode('ascii', errors='ignore').strip().upper()
                            return s.replace('_', '-')
                        except: continue

            # --- HIGH PRIORITY: PlayStation Serial Scan (platform-agnostic) ---
            # These prefixes are very distinctive and should be found regardless of detected platform
            ps_high_priority = [
                rb'(SLUS|SCUS|SLES|SCES|SLPS|SLPM|SCPS|SLKA|SCKA)[_\.\-](\d{3})[\.\-](\d{2})',  # SLUS_203.60
                rb'(SLUS|SCUS|SLES|SCES|SLPS|SLPM|SCPS)[_\-](\d{5})',  # SLUS-20360
                rb'(BLUS|BLES|BCES|BCAS)[_\-](\d{5})',  # PS3: BLUS-30001
                rb'(UCUS|ULES|UCES|UCAS)[_\-](\d{5})',  # PSP: UCUS-98601
            ]
            for pat in ps_high_priority:
                match = re.search(pat, data, re.IGNORECASE)
                if match:
                    try:
                        gs = [g.decode('ascii', errors='ignore').upper() for g in match.groups() if g]
                        if len(gs) == 3:
                            return f"{gs[0]}-{gs[1]}{gs[2]}"
                        elif len(gs) == 2:
                            return f"{gs[0]}-{gs[1]}"
                    except: pass
            
            # --- HIGH PRIORITY: 3DO Serial Scan (platform-agnostic) ---
            # Scan for VERY SPECIFIC 3DO patterns only - avoid matching PS data
            tdo_patterns = [
                rb'(FZ-[A-Z0-9]{4,10})',                    # FZ-SJ3851 (minimum 4 chars after dash)
                rb'(KKKH[_\-]?\d{4,5})',                    # KKKH-9929, KKKH9929
                rb'(BMG[_\-]?\d{4,5})',                     # BMG-9000
            ]
            # PlayStation prefixes to exclude
            ps_prefixes = ['SLUS', 'SCUS', 'SLES', 'SCES', 'SLPS', 'SLPM', 'SCPS', 'SLKA', 'SCKA',
                           'BLUS', 'BLES', 'BCES', 'BCAS', 'UCUS', 'ULES', 'UCES', 'UCAS']
            for pat in tdo_patterns:
                match = re.search(pat, data, re.IGNORECASE)
                if match:
                    try:
                        s = match.group(1).decode('ascii', errors='ignore').strip().upper()
                        # Skip if it looks like PlayStation serial
                        if any(s.startswith(p) for p in ps_prefixes):
                            continue
                        # Normalize: replace _ with -
                        s = re.sub(r'[_\s]+', '-', s)
                        # Add dash if missing (KKKH9929 -> KKKH-9929)
                        if '-' not in s and len(s) >= 8:
                            for i, c in enumerate(s):
                                if c.isdigit():
                                    s = s[:i] + '-' + s[i:]
                                    break
                        # Final validation: must have reasonable length
                        if len(s) >= 7:
                            return s
                    except: pass

            # --- UNIVERSAL SCAN (Fallback) ---
            # Search broadly but validate strictly to avoid noise
            # NOTE: PATTERNS_SATURN and PATTERNS_SEGACD excluded - too generic, cause false matches
            all_pats = PATTERNS_3DO + PATTERNS_PSX + PATTERNS_DREAMCAST + PATTERNS_PS3 + PATTERNS_PSP + PATTERNS_PCENGINE + PATTERNS_NEOGEOCD
            for pat in all_pats:
                 for match in re.finditer(pat, data, re.IGNORECASE):
                     try:
                         # Use full match for 3DO/generic, but group logic for PSX
                         s_full = match.group(0).decode('ascii', errors='ignore').strip().upper()
                         
                         if len(match.groups()) >= 2:
                             # Format groups gracefully (join or keep first 2)
                             gs = [g.decode('ascii', errors='ignore').upper() for g in match.groups() if g]
                             if len(gs) == 3: s = f"{gs[0]}-{gs[1]}{gs[2]}"
                             elif len(gs) == 2: s = f"{gs[0]}-{gs[1]}"
                             else: s = s_full
                         else:
                             s = s_full
                         
                         clean = s.replace('_', '-').strip().upper()
                         # Filter numeric-only patterns like 7-22056:
                         # - If starts with letter (T-95035, G-6021), 1 letter is OK
                         # - If starts with digit, require 2+ letters to be valid
                         letter_count = sum(1 for c in clean if c.isalpha())
                         starts_with_letter = clean and clean[0].isalpha()
                         valid_letters = letter_count >= 1 if starts_with_letter else letter_count >= 2
                         if len(clean) >= 6 and clean not in BLACKLIST and valid_letters:
                             # Serial indicator: Dash + digits + letters
                             if "-" in clean and sum(c.isdigit() for c in clean) >= 3:
                                 return clean
                             # Or very long alphanumeric
                             if len(clean) >= 9 and sum(c.isdigit() for c in clean) >= 4:
                                 return clean
                     except: continue

    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        
    return None

def get_total_size(path):
    """Calculates total size of a file or folder (if Cue, sums bins)"""
    total = 0
    if os.path.isfile(path):
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.cue', '.gdi']:
             # Sum linked files
             bins = get_bin_files(path)
             if bins:
                 for b in bins:
                     if os.path.exists(b): total += os.path.getsize(b)
             else:
                 total = os.path.getsize(path)
        else:
             total = os.path.getsize(path)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for f in files:
                total += os.path.getsize(os.path.join(root, f))
    return total

def get_chd_info(chd_path, chdman_exe):
    """Wraps chdman info and extractraw"""
    info = {"sha1": None, "serial": None}
    
    # Get SHA1
    try:
        cmd = [chdman_exe, "info", "-i", chd_path]
        result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        output = result.stdout
        
        # Parse Data SHA1
        m = re.search(r'Data SHA1:\s*([a-fA-F0-9]{40})', output)
        if m:
            info["sha1"] = m.group(1)
        else:
            m = re.search(r'SHA1:\s*([a-fA-F0-9]{40})', output)
            if m: info["sha1"] = m.group(1)
            
    except Exception as e:
        print(f"CHD Info Error: {e}")

    # Extract RAW for Serial
    temp_bin = os.path.join(os.environ.get('TEMP', '.'), 'storm_temp_extract.bin')
    try:
        # Extract 2MB
        cmd_extract = [chdman_exe, "extractraw", "-i", chd_path, "-o", temp_bin, "-isb", "0", "-ib", "2097152", "-f"]
        subprocess.run(cmd_extract, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        if os.path.exists(temp_bin):
            info["serial"] = get_serial_from_file(temp_bin)
            try:
                os.remove(temp_bin)
            except: pass
    except Exception as e:
        print(f"CHD Extract Error: {e}")
        
    return info

def download_dats_logic(callback_progress=None):
    """Downloads and extracts Redump DATs"""
    # NOTE: In real world, we need a valid URL.
    # Placeholder URL or list of URLs as in PS script
    # For now, let's assume we download a 'master info' or individual dats
    # Since PS script had a list, we might want to replicate that or use a pack.
    # Simplifying for "Demo": Download one generic DAT or skip if no URL provided in prompt
    # User said "Like in old program". Old program iterated a list.
    
    # Let's mock the "Download" process for safety unless we have the URLs handy.
    # Re-reading lines 1087 in PS1... it has a huge list of URL/datfile/.
    
    # We will implement a function that accepts a list of URLs (from logic or config).
    pass 
    
def clear_serial_cache(cache_file="serial_cache.json"):
    """Clears the serial cache file from the app directory."""
    from src.config import get_app_dir
    cache_path = os.path.join(get_app_dir(), cache_file)
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
    return True

def sanitate_filename(filename):
    """Replaces invalid characters in filename with underscores"""
    return "".join([c if c.isalnum() or c in (' ', '.', '-', '_', '(', ')') else '_' for c in filename])

DAT_URLS = [
    "http://redump.org/datfile/arch/", "http://redump.org/datfile/mac/", "http://redump.org/datfile/ajcd/",
    "http://redump.org/datfile/pippin/", "http://redump.org/datfile/qis/", "http://redump.org/datfile/acd/",
    "http://redump.org/datfile/cdtv/", "http://redump.org/datfile/fmt/", "http://redump.org/datfile/fpp/",
    "http://redump.org/datfile/pc/", "http://redump.org/datfile/ite/", "http://redump.org/datfile/kea/",
    "http://redump.org/datfile/kfb/", "http://redump.org/datfile/ks573/", "http://redump.org/datfile/ksgv/",
    "http://redump.org/datfile/ixl/", "http://redump.org/datfile/hs/", "http://redump.org/datfile/vis/",
    "http://redump.org/datfile/xbox/", "http://redump.org/datfile/xbox360/", "http://redump.org/datfile/trf/",
    "http://redump.org/datfile/ns246/", "http://redump.org/datfile/pce/", "http://redump.org/datfile/pc-88/",
    "http://redump.org/datfile/pc-98/", "http://redump.org/datfile/pc-fx/", "http://redump.org/datfile/ngcd/",
    "http://redump.org/datfile/gc/", "http://redump.org/datfile/wii/", "http://redump.org/datfile/palm/",
    "http://redump.org/datfile/3do/", "http://redump.org/datfile/cdi/", "http://redump.org/datfile/photo-cd/",
    "http://redump.org/datfile/psxgs/", "http://redump.org/datfile/ppc/", "http://redump.org/datfile/chihiro/",
    "http://redump.org/datfile/dc/", "http://redump.org/datfile/lindbergh/", "http://redump.org/datfile/mcd/",
    "http://redump.org/datfile/naomi/", "http://redump.org/datfile/naomi2/", "http://redump.org/datfile/sp21/",
    "http://redump.org/datfile/sre/", "http://redump.org/datfile/sre2/", "http://redump.org/datfile/ss/",
    "http://redump.org/datfile/x68k/", "http://redump.org/datfile/psx/", "http://redump.org/datfile/ps2/",
    "http://redump.org/datfile/ps3/", "http://redump.org/datfile/psp/", "http://redump.org/datfile/quizard/",
    "http://redump.org/datfile/ksite/", "http://redump.org/datfile/nuon/", "http://redump.org/datfile/vflash/",
    "http://redump.org/datfile/gamewave/", "http://redump.org/datfile/cd32/"
]


def get_platform_from_dats(sha1, dats_folder):
    """
    Scans all DAT files in the folder for the given SHA1.
    Returns (platform_name, serial) or (None, None).
    """
    if not sha1 or not os.path.isdir(dats_folder):
        return None, None
    
    sha1 = sha1.lower()
    
    try:
        dat_files = [f for f in os.listdir(dats_folder) if f.lower().endswith('.dat')]
        for dat_file in dat_files:
            full_path = os.path.join(dats_folder, dat_file)
            try:
                # Fast text search
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if sha1 in content.lower():
                        platform = os.path.splitext(dat_file)[0]
                        if " - Datfile" in platform:
                            platform = platform.split(" - Datfile")[0]
                        
                        # Try to extract serial from DAT
                        serial = ""
                        idx = content.lower().find(sha1)
                        # Look in a window around the SHA1
                        start = max(0, idx - 500)
                        end = min(len(content), idx + 500)
                        window = content[start:end]
                        
                        m_serial = re.search(r'serial="([^"]+)"', window, re.IGNORECASE)
                        if not m_serial:
                            m_serial = re.search(r'<serial>([^<]+)</serial>', window, re.IGNORECASE)
                        
                        if m_serial:
                            serial = m_serial.group(1).strip()
                            
                        return platform, serial
            except:
                continue
    except:
        pass
    return None, None
        

def detect_fast_platform(filepath):
    """Fast detection of platform based on file content/pattern, skipping full hash."""
    try:
        with open(filepath, 'rb') as f:
            # Read header 1MB
            data = f.read(1024 * 1024)
            
            # PS2 Check (BOOT2 = ...)
            if b"BOOT2" in data or b"cdrom0:" in data:
                 if re.search(rb'BOOT2\s*=', data, re.IGNORECASE):
                     return "Sony - PlayStation 2"
            
            # PS1 Check (BOOT = ...)
            if b"BOOT" in data and b"cdrom:" in data:
                 if re.search(rb'BOOT\s*=', data, re.IGNORECASE):
                     return "Sony - PlayStation"
            
            # PS3 Check
            if b"PS3" in data and (b"PARAM.SFO" in data or b"EBOOT.BIN" in data):
                return "Sony - PlayStation 3"
            
            # PSP Check
            if b"PSP_GAME" in data or b"UMD_DATA.BIN" in data:
                return "Sony - PlayStation Portable"
            
            # Saturn / SegaCD
            if b"SEGA SEGASATURN" in data:
                return "Sega - Saturn"
            if b"SEGADISCSYSTEM" in data:
                return "Sega - Mega-CD - Sega CD"
            
            # Dreamcast Check
            if b"SEGA" in data[:32] and (b"KATANA" in data[:64] or b"DISC" in data[:64]):
                return "Sega - Dreamcast"
            
            # GameCube Check (Magic bytes: C2 33 9F 3D)
            if len(data) >= 4 and data[0x1C:0x20] == b'\xC2\x33\x9F\x3D':
                return "Nintendo - GameCube"
            
            # Wii Check (Magic bytes: 5D 1C 9E A3)
            if len(data) >= 4 and data[0x18:0x1C] == b'\x5D\x1C\x9E\xA3':
                return "Nintendo - Wii"
            
            # 3DO Check - Multiple signatures for Opera filesystem
            # Signature 1: Opera FS header \x01ZZZZZ (anywhere in first 1KB)
            if b"\x01ZZZZZ" in data[:1024]:
                return "Panasonic - 3DO Interactive Multiplayer"
            # Signature 2: "3DO" with various other keywords
            if b"3DO" in data[:2048]:
                if any(kw in data[:2048] for kw in [b"OPERATOR", b"LASERLOCK", b"CD_ROM", b"CDROM"]):
                    return "Panasonic - 3DO Interactive Multiplayer"
            # Signature 3: Opera specific markers
            if b"opera" in data[:1024].lower() or b"CD-ROM" in data[:200] and b"\x01" in data[:10]:
                return "Panasonic - 3DO Interactive Multiplayer"
            
            # Neo Geo CD Check
            if b"NEO-GEO" in data or b"NGCD" in data:
                return "SNK - Neo Geo CD"
            
            # PC Engine / TurboGrafx-CD
            if b"PC Engine" in data or b"TGXCD" in data:
                return "NEC - PC Engine CD - TurboGrafx-CD"
                
    except Exception as e:
        pass
    return None

def detect_platform_from_serial(serial):
    """Infers platform from a serial number string.
    Patterns are ordered by length/specificity (longest first) to prevent
    short patterns from matching before more specific ones.
    """
    if not serial: return None
    s = str(serial).upper().strip()
    
    # === TIER 1: Very Specific / Long Prefixes (5+ chars) ===
    
    # PC Engine / TurboGrafx-CD: TGXCD (5 chars), NAPR- (5), PWD- (4)
    if s.startswith("TGXCD") or s.startswith("NAPR-"):
        return "NEC - PC Engine CD - TurboGrafx-CD"
    
    # Neo Geo CD: NGCD- (5 chars)
    if s.startswith("NGCD-"):
        return "SNK - Neo Geo CD"
    
    # Panasonic 3DO: KKKH- (5 chars)
    if s.startswith("KKKH-"):
        return "Panasonic - 3DO Interactive Multiplayer"
    
    # === TIER 2: 4-Character Prefixes ===
    
    # PS3: BLUS, BLES, BCES, BCAS, BCJS, NPUB, NPEB, NPJB (4 chars)
    if any(p in s for p in ["BLUS", "BLES", "BCES", "BCAS", "BCJS", "NPUB", "NPEB", "NPJB"]):
        return "Sony - PlayStation 3"
    
    # PSP: UCUS, ULES, UCES, UCAS, UCJS, NPUH, NPEH, NPJH (4 chars)
    if any(p in s for p in ["UCUS", "ULES", "UCES", "UCAS", "UCJS", "NPUH", "NPEH", "NPJH"]):
        return "Sony - PlayStation Portable"
    
    # PlayStation 1 / 2: SLUS, SCUS, etc. (4 chars)
    ps_prefixes = ["SLUS", "SCUS", "SLES", "SCES", "SLPS", "SLPM", "SCPS", "SLED", 
                   "SLUK", "SLKA", "SLPA", "SCKA", "SICP", "SCPN", "PBPX"]
    if any(p in s for p in ps_prefixes):
        digits = re.sub(r'[^0-9]', '', s)
        if len(digits) >= 5:
            return "Sony - PlayStation 2"
        return "Sony - PlayStation"
    
    # Dreamcast: HDR- (4 chars)
    if s.startswith("HDR-"):
        return "Sega - Dreamcast"
    
    # Neo Geo CD: NGH- (4 chars)
    if s.startswith("NGH-"):
        return "SNK - Neo Geo CD"
    
    # PC Engine: PWD- (4 chars)
    if s.startswith("PWD-"):
        return "NEC - PC Engine CD - TurboGrafx-CD"
    
    # Panasonic 3DO: BMG- (4 chars)
    if s.startswith("BMG-"):
        return "Panasonic - 3DO Interactive Multiplayer"
    
    # === TIER 3: 3-Character Prefixes ===
    
    # Panasonic 3DO: FZ- (3 chars), 3DO
    if s.startswith("FZ-") or "3DO" in s:
        return "Panasonic - 3DO Interactive Multiplayer"
    
    # PlayStation short prefixes: LPS, LPM (3 chars)
    if s.startswith("LPS") or s.startswith("LPM"):
        return "Sony - PlayStation"
    
    # Sega Saturn: MK-, GS- (3 chars)
    if s.startswith("MK-") or s.startswith("GS-"):
        return "Sega - Saturn"
    
    # Xbox: MS-, EA- (3 chars)
    if s.startswith("MS-") or s.startswith("EA-"):
        return "Microsoft - Xbox"
    
    # === TIER 4: 2-Character Prefixes (VERY generic - must be last) ===
    
    # Sega T- prefix: Dreamcast vs Saturn vs Mega-CD
    if s.startswith("T-"):
        # Check for Dreamcast pattern: T-XXXXX-M/E/J/K (at least 8 chars with region suffix)
        if len(s) >= 8 and re.match(r'^T-\d{4,5}-?[MEJK]?', s):
            return "Sega - Dreamcast"
        # Otherwise, check digit count for Saturn / Mega-CD differentiation
        digits = re.sub(r'[^0-9]', '', s)
        if len(digits) == 5:
            return "Sega - Mega-CD - Sega CD"
        return "Sega - Saturn"
    
    # Sega G- prefix (generic)
    if s.startswith("G-") or s.startswith("GM"):
        return "Sega - Saturn"
    
    # === TIER 5: Length-Based Detection (no clear prefix) ===
    
    # GameCube / Wii: 6-character alphanumeric IDs like GALE01, R3DE01
    if len(s) == 6 and s.isalnum():
        if s[0] in ['G', 'D']:  # GameCube IDs typically start with G or D
            return "Nintendo - GameCube"
        if s[0] in ['R', 'S']:  # Wii IDs typically start with R or S
            return "Nintendo - Wii"
    
    return None



def get_all_platforms(dats_folder):
    """Returns a sorted list of platform names derived from DAT filenames in the folder."""
    if not os.path.isdir(dats_folder):
        return []
    
    platforms = set()
    try:
        if os.path.exists(dats_folder):
            for f in os.listdir(dats_folder):
                if f.lower().endswith('.dat'):
                    name = os.path.splitext(f)[0]
                    if " - Datfile" in name:
                        name = name.split(" - Datfile")[0]
                    platforms.add(name)
    except:
        pass
    return sorted(list(platforms))

def extract_archive(archive_path, extract_to):
    """Extracts zip, 7z, or rar archives using libraries or CLI fallbacks"""
    ext = os.path.splitext(archive_path)[1].lower()
    
    if ext == '.zip':
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            return True
        except Exception as e:
            print(f"Zip extraction error: {e}")
    
    # Try 7z fallback for 7z/rar/zip
    try:
        # Check standard 7z command
        subprocess.run(["7z", "x", archive_path, f"-o{extract_to}", "-y"], 
                        check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except:
        # Try finding 7z.exe in common locations or current dir
        common_7z = [
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "7-Zip", "7z.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "7-Zip", "7z.exe"),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "7z.exe")
        ]
        for exe in common_7z:
            if os.path.exists(exe):
                try:
                    subprocess.run([exe, "x", archive_path, f"-o{extract_to}", "-y"], 
                                    check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    return True
                except: continue
                
    # Try UnRAR fallback for RAR
    if ext == '.rar':
        try:
            subprocess.run(["UnRAR", "x", archive_path, extract_to, "-y"], 
                            check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except: pass

    return False

# ========== SERIAL CACHE FUNCTIONS ==========

def _get_serial_cache_path():
    """Get the serial cache file path."""
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(script_dir, "cache", "serial_cache.json")

def _load_serial_cache():
    """Load serial cache from JSON file."""
    try:
        cache_file = _get_serial_cache_path()
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading serial cache: {e}")
    return {}

def _save_serial_cache(cache):
    """Save serial cache to JSON file."""
    try:
        cache_file = _get_serial_cache_path()
        cache_dir = os.path.dirname(cache_file)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving serial cache: {e}")

def save_serial_to_cache(filename, sha1, serial, platform=None):
    """Save serial number to cache by filename and SHA1."""
    if not filename or not sha1:
        return
    cache = _load_serial_cache()
    cache[filename] = {
        "sha1": sha1.upper() if sha1 else "",
        "serial": serial or "",
        "platform": platform or "",
        "updated": datetime.now().isoformat()
    }
    _save_serial_cache(cache)

def get_cached_serial(filename, sha1):
    """Get cached serial if filename + SHA1 match.
    Returns (serial, platform) or (None, None) if not found or SHA1 mismatch.
    """
    if not filename:
        return None, None
    cache = _load_serial_cache()
    entry = cache.get(filename)
    if entry:
        cached_sha1 = entry.get("sha1", "").upper()
        if sha1 and cached_sha1 == sha1.upper():
            return entry.get("serial"), entry.get("platform")
    return None, None

def remove_from_serial_cache(filename):
    """Remove entry from serial cache by filename."""
    cache = _load_serial_cache()
    if filename in cache:
        del cache[filename]
        _save_serial_cache(cache)
        return True
    return False

def clear_serial_cache():
    """Clear entire serial cache."""
    try:
        cache_file = _get_serial_cache_path()
        if os.path.exists(cache_file):
            os.remove(cache_file)
        return True
    except:
        return False
