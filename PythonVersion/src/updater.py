import os
import sys
import json
import time
import subprocess
import urllib.request
from PyQt6.QtCore import QThread, pyqtSignal

# GitHub API
REPO_OWNER = "ReiKatari"
REPO_NAME = "STORM_CHDMan"
RELEASES_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

class UpdateThread(QThread):
    checkFinished = pyqtSignal(bool, str, str) # has_update, version, download_url
    
    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version

    def run(self):
        try:
            # Check GitHub
            with urllib.request.urlopen(RELEASES_URL, timeout=10) as response:
                if response.status != 200:
                    self.checkFinished.emit(False, "", "")
                    return
                
                data = json.loads(response.read().decode())
                
                tag_name = data.get("tag_name", "").replace("v", "").strip()
                assets = data.get("assets", [])
                
                # Check version (Simple string compare or loose check)
                # Assuming tag is e.g. "1.1" and current is "1.0"
                # Semantic Version Check
                def parse_ver(v):
                    try: 
                        return [int(x) for x in v.replace('v','').split('.')]
                    except: 
                        return [0,0,0]

                remote = parse_ver(tag_name)
                local = parse_ver(self.current_version)
                
                if remote > local:
                    # Find exe asset
                    download_url = ""
                    for asset in assets:
                         if asset["name"].endswith(".exe"):
                             download_url = asset["browser_download_url"]
                             break
                    
                    if download_url:
                        self.checkFinished.emit(True, tag_name, download_url)
                    else:
                        self.checkFinished.emit(False, "", "")
                else:
                    self.checkFinished.emit(False, "", "")
                    
        except Exception as e:
            # Handle Rate Limit gracefully
            if "HTTP Error 403" in str(e):
                print("GitHub Status: Rate Limit Exceeded (Skipping update check)")
                self.checkFinished.emit(False, "", "")
                return
                
            print(f"Update check failed: {e}")
            self.checkFinished.emit(False, "", "")

class UpdateDownloadThread(QThread):
    progress = pyqtSignal(int, int) # downloaded, total
    finished = pyqtSignal(bool, str) # success, error_msg

    def __init__(self, url, dest):
        super().__init__()
        self.url = url
        self.dest = dest

    def run(self):
        try:
            req = urllib.request.Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                total_size = int(response.info().get('Content-Length', 0))
                downloaded = 0
                chunk_size = 1024 * 64
                
                with open(self.dest, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total_size)
            
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))

def perform_update_safe(download_url):
    """
    Creates an external batch file to handle the update process:
    1. Waits for this process to exit.
    2. Moves the new executable over the current one.
    3. Restarts the application with a clean environment.
    """
    try:
        current_exe = sys.executable
        app_dir = os.path.dirname(current_exe)
        new_exe_name = os.path.join(app_dir, "STORM_CHDMan.new")
        bat_path = os.path.join(app_dir, "updater.bat")
        current_pid = os.getpid()
        exe_name = os.path.basename(current_exe)
        
        # Create a robust batch file
        with open(bat_path, "w", encoding="cp1251") as bat:
            bat.write("@echo off\n")
            bat.write("title STORM CHDMan Updater\n")
            bat.write("echo Waiting for application to exit...\n")
            bat.write(f"set OLD_PID={current_pid}\n")
            
            # 1. Wait for process to die
            bat.write(":wait_loop\n")
            bat.write('tasklist /fi "pid eq %OLD_PID%" | find "%OLD_PID%" > nul\n')
            bat.write("if not errorlevel 1 (\n")
            bat.write("    timeout /t 1 /nobreak > nul\n")
            bat.write("    goto wait_loop\n")
            bat.write(")\n")
            
            # 2. Replace file
            bat.write("echo Updating files...\n")
            bat.write(":replace_loop\n")
            bat.write(f'move /y "{new_exe_name}" "{current_exe}" > nul\n')
            bat.write("if errorlevel 1 (\n")
            bat.write("    echo Retry move...\n")
            bat.write("    timeout /t 1 /nobreak > nul\n")
            bat.write("    goto replace_loop\n")
            bat.write(")\n")
            
            # 3. Clean environment and restart
            # Crucial: Unset PyInstaller variables so the new process doesn't try to reuse our temp dir
            bat.write("set _MEIPASS=\n")
            bat.write("set PYTHONPATH=\n")
            bat.write("set PYTHONHOME=\n")
            
            bat.write("echo Starting new version...\n")
            bat.write(f'start "" "{current_exe}"\n')
            
            # 4. Self-destruct
            bat.write("echo Done.\n")
            bat.write(f'(goto) 2>nul & del "{bat_path}"\n')

        # Launch the batch file detached
        if sys.platform == 'win32':
            os.startfile(bat_path)
        else:
            subprocess.Popen(['open', bat_path]) # fallback/mac
            
        # Exit immediately
        sys.exit(0)
        
    except Exception as e:
        print(f"Update failed: {e}")
        return False
