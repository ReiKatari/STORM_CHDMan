# src/config.py
import json
import os
import locale
import sys

def get_app_dir():
    """Returns the directory where the EXE or script is located."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # If running from src/config.py, go up to project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_resource_path(relative_path):
    """Returns the path to a bundled resource (in _MEIPASS) or local file."""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    # In dev mode, resources are in the project root
    return os.path.join(get_app_dir(), relative_path)

class Config:
    def __init__(self):
        self.settings_file = os.path.join(get_app_dir(), "settings.json")
        self.language = "EN"
        self.output_folder = ""
        self.window_size = (1450, 800)
        self.check_updates = True
        
        # New Settings
        self.threads = os.cpu_count() or 0 # Default to max threads
        self.compression = "lzma" # lzma, zlib
        self.hunk_cd = "1047744"
        self.hunk_dvd = "1048576"
        self.force_overwrite = False
        self.platform_recognition = True
        self.preset_aethersx2 = False
        self.notify_text = True
        self.notify_sound = False
        self.auto_update = True
        self.column_widths = []
        self.preset_column_widths = []
        self.theme = "Steel Storm"
        
        # v1.1.0 Settings
        self.minimize_to_tray = False
        self.close_to_tray = False
        self.log_font_size = 10
        self.log_font_enabled = False
        self.extract_subfolders = False
        self.delete_source = False
        self.platform_output_folders = [] # List of dicts
        self.large_font = False # +4pt font size
        
        # Detect system language
        sys_lang = locale.getdefaultlocale()[0]
        if sys_lang and "ru" in sys_lang.lower():
            self.language = "RU"
        
        self.load()

    def load(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.language = data.get("language", self.language)
                    self.output_folder = data.get("output_folder", "")
                    self.window_size = tuple(data.get("window_size", [1200, 800]))
                    self.column_widths = data.get("column_widths", [])
                    
                    self.threads = data.get("threads", 0)
                    self.compression = data.get("compression", "lzma")
                    self.hunk_cd = data.get("hunk_cd", "2352")
                    self.hunk_dvd = data.get("hunk_dvd", "4096")
                    self.force_overwrite = data.get("force_overwrite", False)
                    self.platform_recognition = data.get("platform_recognition", True)
                    self.preset_aethersx2 = data.get("preset_aethersx2", False)
                    self.notify_text = data.get("notify_text", True)
                    self.notify_sound = data.get("notify_sound", False)
                    self.auto_update = data.get("auto_update", False)
                    self.preset_column_widths = data.get("preset_column_widths", [])
                    self.theme = data.get("theme", "Dark")
                    
                    self.minimize_to_tray = data.get("minimize_to_tray", False)
                    self.close_to_tray = data.get("close_to_tray", False)
                    self.log_font_size = data.get("log_font_size", 10)
                    self.log_font_enabled = data.get("log_font_enabled", False)
                    self.extract_subfolders = data.get("extract_subfolders", False)
                    self.delete_source = data.get("delete_source", False)
                    self.platform_output_folders = data.get("platform_output_folders", [])
            except:
                pass

    def save(self):
        data = {
            "language": self.language,
            "output_folder": self.output_folder,
            "window_size": self.window_size,
            "column_widths": self.column_widths,
            "preset_column_widths": self.preset_column_widths,
            "threads": self.threads,
            "compression": self.compression,
            "hunk_cd": self.hunk_cd,
            "hunk_dvd": self.hunk_dvd,
            "force_overwrite": self.force_overwrite,
            "platform_recognition": self.platform_recognition,
            "preset_aethersx2": self.preset_aethersx2,
            "notify_text": self.notify_text,
            "notify_sound": self.notify_sound,
            "auto_update": self.auto_update,
            "theme": self.theme,
            "minimize_to_tray": self.minimize_to_tray,
            "close_to_tray": self.close_to_tray,
            "log_font_size": self.log_font_size,
            "log_font_enabled": self.log_font_enabled,
            "extract_subfolders": self.extract_subfolders,
            "delete_source": self.delete_source,
            "platform_output_folders": self.platform_output_folders
        }
        
        # 1. Save main file
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        # 2. Create Backup
        try:
             backup_file = self.settings_file + ".bak"
             import shutil
             shutil.copy2(self.settings_file, backup_file)
        except: pass

# Global translations dictionary
TRANSLATIONS = {
    "RU": {
        "WindowTitle": "STORM CHDMan",
        "btnAddFiles": "Добавить файлы",
        "btnAddFolder": "Добавить папку",
        "btnClear": "Очистить список",
        "btnSettings": "Настройки",
        "btnStart": "НАЧАТЬ ОБРАБОТКУ",
        "btnStop": "ОСТАНОВИТЬ",
        "btnPause": "Пауза",
        "btnCancel": "Отмена",
        "btnClose": "Закрыть",
        "btnDownloadDATs": "Скачать DAT-файлы",
        "btnDeleteDATs": "Удалить DAT-файлы",
        "btnClearCache": "Очистить кэш серийников",
        
        "tabMain": "Обработка",
        "tabSettings": "Настройки",
        
        "grpPaths": "Пути",
        "grpProcessing": "Параметры обработки",
        "grpNotification": "Уведомления и вид",
        "grpLanguage": "Язык",
        "grpTray": "Системный трей",
        "grpGeneralInfo": "Общая информация",
        
        "lblOutput": "Выходная папка:",
        "lblThreads": "Потоки (CPU):",
        "lblCompression": "Алгоритм сжатия:",
        "lblHunkCD": "Размер блока CD:",
        "lblHunkDVD": "Размер блока DVD:",
        "lblLanguage": "Язык интерфейса:",
        "chkLargeFont": "Крупный шрифт",
        
        "chkOverwrite": "Принудительная перезапись файлов",
        "chkRecognition": "Распознавание платформ по DAT-файлам",
        "chkAetherSX2": "AetherSX2 / NetherSX2 (Авто-настройка)",
        "chkNotifyText": "Текстовое уведомление по завершению",
        "chkNotifySound": "Звуковое уведомление (notification.wav)",
        "chkMinimizeTray": "Сворачивать в трей",
        "chkCloseTray": "Закрывать в трей",
        "chkLogFont": "Размер шрифта логов",
        "chkExtractSubfolders": "Извлекать в папку с именем файла",
        "chkDeleteSource": "Удалять исходные файлы после обработки",
        
        "menuFile": "Файл",
        "menuTools": "Инструменты",
        "menuHelp": "Справка",
        "menuAbout": "О программе",
        
        "colFile": "Файл (можно переименовать)",
        "colStartSize": "Нач. размер",
        "colEndSize": "Кон. размер",
        "colDiff": "Разница",
        "colStatus": "Статус",
        "colPlatform": "Платформа",
        "colFormat": "Формат",
        "colSHA1": "SHA1",
        "colSerial": "Серийный номер",
        "colCount": "Кол-во",
        
        "StatusAdded": "Ожидание",
        "StatusProcessing": "В работе...",
        "StatusDone": "Готово",
        "StatusError": "Ошибка",
        "StatusAnalyzing": "Анализ...",
        "StatusHashing": "Хеширование...",
        "StatusScanning": "Поиск серийника...",
        "StatusScanningFiles": "Сканирование...",
        "StatusReady": "Готово к старту",
        "StatusCancelled": "Отменено",
        "StatusSkipped": "Ранее обработано",
        "StatusNoDAT": "Нет DAT-файла",
        "StatusExtracting": "Извлечение...",
        "LogTime": "Время выполнения:",
        "LogStarted": "Начало логов",
        "LogAdded": "Добавлено:",
        "LogAnalyzing": "Анализ:",
        "LogHashed": "SHA1:",
        "LogPlatform": "Платформа:",
        
        "lblTotalStartSize": "Общий Нач. размер:",
        "lblTotalEndSize": "Общий Кон. размер:",
        "lblTotalDiff": "Общая Разница:",
        "lblTotalTasks": "Всего задач:",
        "lblFinishedTasks": "Готово задач:",
        "lblInProgressTasks": "В работе задач:",
        
        "menuContextProcess": "Обработать",
        "menuContextRehash": "Перехэшировать",
        "menuContextOpenFolder": "Открыть папку с файлом",
        
        "LogReady": "Добавьте файлы (Drag & Drop) и нажмите НАЧАТЬ.",
        "MsgSerialNotFound": "Серийный номер не найден",
        "MsgConfirmDelDAT": "Вы уверены, что хотите удалить все DAT-файлы?",
        "MsgDatsDownloaded": "Все DAT-файлы скачаны",
        "MsgCacheCleared": "Кэш серийных номеров очищен.",
        "MsgWaitForDownload": "Дождитесь скачивания всех DAT-файлов.",
        "MsgDoneTitle": "Обработка завершена",
        "MsgDoneBody": "Все задачи выполнены.",
        "MsgDATsDeleted": "Все DAT-файлы удалены.",
        "grpTheme": "Тема",
        "lblTheme": "Тема:",
        "lblAuthor": "Автор:",
        
        "grpUpdates": "Обновление",
        "chkAutoUpdate": "Авто-обновление",
        "dlgUpdateTitle": "Доступно обновление",
        "dlgUpdateMsg": "Доступна новая версия STORM CHDMan!",
        "dlgUpdateCur": "Текущая версия",
        "dlgUpdateNew": "Новая версия",
        "btnUpdate": "Обновить",
        
        "grpPresets": "Пресеты платформ",
        "grpOutputFolders": "Выходные папки для платформ",
        "btnAddPreset": "Добавить",
        "btnDelPreset": "Удалить",
        "btnExpand": "Развернуть",
        "btnCollapse": "Свернуть",
        "colEnabled": "Вкл",
        "colPlatform": "Платформа",
        "colAlgo": "Алгоритм сжатия",
        "colHunkCD": "Размер блока CD",
        "colHunkDVD": "Размер блока DVD",
        "colComment": "Комментарий",
        "colOutput": "Выходная папка",
        "btnBrowse": "...",

        "grpFileOps": "Файлы и распознавание",
        "grpCompressionSettings": "Параметры сжатия",
        "grpHunkSettings": "Размеры блоков",

        "menuContextDelete": "Удалить строку (Del)",
        "menuContextOpenSrc": "Открыть папку с файлом"
    },
    "EN": {
        "WindowTitle": "STORM CHDMan",
        "btnAddFiles": "Add Files",
        "btnAddFolder": "Add Folder",
        "btnClear": "Clear List",
        "btnSettings": "Settings",
        "btnStart": "START PROCESSING",
        "btnStop": "STOP",
        "btnPause": "Pause",
        "btnCancel": "Cancel",
        "btnClose": "Close",
        "btnDownloadDATs": "Download DATs",
        "btnDeleteDATs": "Delete DATs",
        "btnClearCache": "Clear Serial Cache",
        
        "tabMain": "Processing",
        "tabLog": "Log",
        "tabSettings": "Settings",
        
        "grpPaths": "Paths",
        "grpProcessing": "Processing Options",
        "grpNotification": "Notifications & Appearance",
        "grpLanguage": "Language",
        "grpTray": "System Tray",
        "grpTheme": "Theme",
        "grpGeneralInfo": "General Information",
        "lblTheme": "Theme:",
        "lblAuthor": "Author:",
        
        "grpUpdates": "Updates",
        "chkAutoUpdate": "Auto-Update",
        "dlgUpdateTitle": "Update Available",
        "dlgUpdateMsg": "A new version of STORM CHDMan is available!",
        "dlgUpdateCur": "Current Version",
        "dlgUpdateNew": "New Version",
        "btnUpdate": "Update",
        
        "lblOutput": "Output Folder:",
        "lblThreads": "Threads (CPU):",
        "lblCompression": "Compression Algo:",
        "lblHunkCD": "Hunk Size CD:",
        "lblHunkDVD": "Hunk Size DVD:",
        "lblLanguage": "Interface Language:",
        "chkLargeFont": "Large Font",
        
        "chkOverwrite": "Force Overwrite Files",
        "chkRecognition": "Platform Recognition (Redump DATs)",
        "chkAetherSX2": "AetherSX2 / NetherSX2 (Auto Settings)",
        "chkNotifyText": "Text Notification",
        "chkNotifySound": "Sound Notification (notification.wav)",
        "chkMinimizeTray": "Minimize to tray",
        "chkCloseTray": "Close to tray",
        "chkLogFont": "Enable custom log font size:",
        "chkExtractSubfolders": "Extract to folder with file name",
        "chkDeleteSource": "Delete source files after processing",
        
        "menuFile": "File",
        "menuTools": "Tools",
        "menuHelp": "Help",
        "menuAbout": "About",
        
        "colFile": "File (renameable)",
        "colStartSize": "Start Size",
        "colEndSize": "End Size",
        "colDiff": "Difference",
        "colStatus": "Status",
        "colPlatform": "Platform",
        "colFormat": "Format",
        "colSHA1": "SHA1",
        "colSerial": "Serial Number",
        "colCount": "Count",
        
        "StatusAdded": "Added",
        "StatusProcessing": "Processing...",
        "StatusDone": "Done",
        "StatusError": "Error",
        "StatusAnalyzing": "Analyzing...",
        "StatusHashing": "Hashing...",
        "StatusScanning": "Scanning Serial...",
        "StatusScanningFiles": "Scanning...",
        "StatusReady": "Ready",
        "StatusCancelled": "Cancelled",
        "StatusSkipped": "Already Processed",
        "StatusNoDAT": "No DAT File",
        "StatusExtracting": "Extracting...",
        "LogTime": "Processing time:",
        "LogStarted": "Start of logs",
        "LogAdded": "Added:",
        "LogAnalyzing": "Analyzing:",
        "LogHashed": "SHA1 calculated:",
        "LogPlatform": "Platform:",
        
        "lblTotalStartSize": "Total Start Size:",
        "lblTotalEndSize": "Total End Size:",
        "lblTotalDiff": "Total Difference:",
        "lblTotalTasks": "Total Tasks:",
        "lblFinishedTasks": "Finished Tasks:",
        "lblInProgressTasks": "In Progress:",
        
        "menuContextProcess": "Process",
        "menuContextRehash": "Rehash",
        "menuContextOpenFolder": "Open Folder",
        
        "LogReady": "Ready. Drag and drop files here.",
        "MsgSerialNotFound": "Serial not found",
        "MsgConfirmDelDAT": "Are you sure you want to delete all DAT files?",
        "MsgCacheCleared": "Serial number cache cleared.",
        "MsgWaitForDownload": "Please wait for DAT files to finish downloading.",
        "MsgDatsDownloaded": "All DAT files downloaded.",
        "MsgDoneTitle": "Processing Complete",
        "MsgDoneBody": "All tasks completed.",
        "MsgDATsDeleted": "All DAT files deleted.",
        
        "grpPresets": "Platform Presets",
        "grpOutputFolders": "Output Folders for Platforms",
        "btnAddPreset": "Add",
        "btnDelPreset": "Delete",
        "colEnabled": "On",
        "colPlatform": "Platform",
        "colAlgo": "Compression Algo",
        "colHunkCD": "Hunk Size CD",
        "colHunkDVD": "Hunk Size DVD",
        "colComment": "Comment",
        "colOutput": "Output Folder",
        "btnBrowse": "...",
        
        "grpFileOps": "Files & Recognition",
        "grpCompressionSettings": "Compression Settings",
        "grpHunkSettings": "Hunk Sizes",
        
        "menuContextDelete": "Delete Row (Del)",
        "menuContextOpenSrc": "Open Source Folder"
    }
}

def T(key, lang="EN"):
    return TRANSLATIONS.get(lang, TRANSLATIONS["EN"]).get(key, key)
