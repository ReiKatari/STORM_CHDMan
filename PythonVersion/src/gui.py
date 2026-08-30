# src/gui.py
import os
import sys 
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, QLabel, 
                             QLineEdit, QHeaderView, QFileDialog, QProgressBar, QMessageBox, QDialog, QProgressDialog, QSystemTrayIcon, QStyle,
                             QGroupBox, QComboBox, QCheckBox, QMenu, QSpinBox, QTabWidget, QApplication, QSizePolicy, QTextEdit, QToolButton, QScrollArea, QFrame, QGridLayout, QCompleter)

from PyQt6.QtCore import Qt, pyqtSignal, QSize, QUrl, QParallelAnimationGroup, QPropertyAnimation, QAbstractAnimation, QTimer
from PyQt6.QtGui import QIcon, QDropEvent, QDragEnterEvent, QAction, QDesktopServices, QShortcut, QKeySequence

from src.config import Config, T, get_app_dir, get_resource_path
from src.themes import THEMES, get_qss
from src.presets import load_presets, save_presets
from src.logic import get_readable_size, get_total_size, clear_serial_cache, sanitate_filename, get_bin_files, get_all_platforms
from src.workers import ScanThread, AnalysisThread, ConversionThread, InfoThread, DownloadThread
from src.updater import UpdateThread, UpdateDownloadThread, perform_update_safe

class DropLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isdir(path):
                self.setText(path)

class UpdateDialog(QDialog):
    def __init__(self, current_ver, new_ver, lang, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T("dlgUpdateTitle", lang))
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel(T("dlgUpdateMsg", lang))
        font = lbl_title.font()
        font.setPointSize(11)
        font.setBold(True)
        lbl_title.setFont(font)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        
        lbl_info = QLabel(f"{T('dlgUpdateCur', lang)}: {current_ver}\n{T('dlgUpdateNew', lang)}: {new_ver}")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Adaptive color for light/dark theme? 
        # But user forced dark theme logic mostly. 
        # Using generic text color or observing theme.
        # Safe to use dynamic qss or just standard. 
        # Using a mid-grey which is visible on both usually, or rely on parent.
        # But forcing style for "rich aesthetics".
        lbl_info.setStyleSheet("margin: 15px; font-weight: bold;")
        layout.addWidget(lbl_info)
        
        btn_layout = QHBoxLayout()
        self.btnUpdate = QPushButton(T("btnUpdate", lang))
        self.btnUpdate.clicked.connect(self.accept)
        self.btnUpdate.setStyleSheet("""
            QPushButton { background-color: #2e7d32; color: white; padding: 8px; border-radius: 4px; font-weight: bold; } 
            QPushButton:hover { background-color: #388e3c; }
        """)
        self.btnUpdate.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.btnCancel = QPushButton(T("btnCancel", lang))
        self.btnCancel.clicked.connect(self.reject)
        self.btnCancel.setStyleSheet("QPushButton { padding: 8px; }")
        self.btnCancel.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_layout.addWidget(self.btnCancel)
        btn_layout.addWidget(self.btnUpdate)
        layout.addLayout(btn_layout)

class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
        super(CollapsibleBox, self).__init__(parent)

        # Header
        self.header_widget = QWidget()
        h_layout = QHBoxLayout(self.header_widget)
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #4da6ff;")
        
        self.btn_expand = QPushButton("Развернуть") 
        self.btn_expand.setCheckable(True)
        self.btn_expand.setFixedWidth(120) # Wider to fit text
        self.btn_expand.toggled.connect(self.on_toggled)
        
        h_layout.addWidget(self.lbl_title)
        h_layout.addStretch()
        h_layout.addWidget(self.btn_expand)

        self.toggle_animation = QParallelAnimationGroup(self)
        
        self.content_area = QWidget()
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)
        self.content_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        lay = QVBoxLayout(self)
        lay.setSpacing(5)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.header_widget)
        lay.addWidget(self.content_area)

        self.toggle_animation.addAnimation(QPropertyAnimation(self.content_area, b"maximumHeight"))
        self.toggle_animation.addAnimation(QPropertyAnimation(self.content_area, b"minimumHeight"))

    def on_toggled(self, checked):
        self.btn_expand.setText("Свернуть" if checked else "Развернуть")
        self.toggle_animation.setDirection(QAbstractAnimation.Direction.Forward if checked else QAbstractAnimation.Direction.Backward)
        self.toggle_animation.start()

    def setContent(self, widget):
        # Clear existing layout/content if any
        if self.content_area.layout():
             QWidget().setLayout(self.content_area.layout()) # Re-parent old layout to trash
             
        lay = QVBoxLayout(self.content_area)
        lay.setContentsMargins(0,0,0,0)
        lay.addWidget(widget)
        
        # Calculate height
        widget.adjustSize()
        content_height = widget.sizeHint().height()
        
        for i in range(self.toggle_animation.animationCount()):
            anim = self.toggle_animation.animationAt(i)
            anim.setDuration(300)
            anim.setStartValue(0)
            anim.setEndValue(content_height)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = Config()
        
        # Cleanup temp extraction folder on startup
        temp_dir = os.path.join(get_app_dir(), "temp_extract")
        if os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except: pass
        
        # Minimize console if present (Windows)
        if sys.platform == "win32":
            try:
                import ctypes
                # SW_MINIMIZE = 6
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 6)
            except:
                pass
        
        # Threads & State
        self.scan_thread = None
        self.analysis_thread = None
        self.conversion_thread = None
        self.download_thread = None
        self.info_thread = None
        self.info_queue = []
        self.analysis_queue = []
        self.existing_paths = set() 
        self.loading_presets = False
        self.is_downloading = False  # Block file adding during DAT download
        self.saved_settings = {} 
        self.VERSION = "1.3.7"
        self.update_thread = None 
        
        self.initMenuBar()
        self.initTray()
        self.initUI()
        self.applyTheme()
        self.center()
        self.center()
        self.updateControls()
        
        if self.cfg.auto_update:
            self.startUpdateCheck()

    def startUpdateCheck(self):
        self.update_thread = UpdateThread(self.VERSION)
        self.update_thread.checkFinished.connect(self.onUpdateCheckFinished)
        self.update_thread.start()

    def onUpdateCheckFinished(self, has_update, version, url):
        if has_update:
            dlg = UpdateDialog(self.VERSION, version, self.cfg.language, self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                # Show Progress Dialog
                self.upd_progress = QProgressDialog(T("dlgUpdateMsg", self.cfg.language), T("btnCancel", self.cfg.language), 0, 100, self)
                self.upd_progress.setWindowModality(Qt.WindowModality.WindowModal)
                self.upd_progress.setWindowTitle("STORM CHDMan Updater")
                self.upd_progress.show()
                
                app_dir = get_app_dir()
                dest = os.path.join(app_dir, "STORM_CHDMan.new")
                
                self.upd_downloader = UpdateDownloadThread(url, dest)
                self.upd_downloader.progress.connect(self.onDownloadUpdateProgress)
                self.upd_downloader.finished.connect(self.onDownloadUpdateFinished)
                self.upd_downloader.start()
                
                # If user cancels the dialog, we might want to stop thread, but simplicity first.

    def onDownloadUpdateProgress(self, current, total):
        if total > 0:
            pct = int((current / total) * 100)
            self.upd_progress.setValue(pct)
            mb_cur = current / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.upd_progress.setLabelText(f"{T('dlgUpdateMsg', self.cfg.language)}\n{mb_cur:.1f} MB / {mb_total:.1f} MB")

    def onDownloadUpdateFinished(self, success, error_msg):
        self.upd_progress.close()
        if success:
            # Re-confirm or just go
            perform_update_safe("") # URL ignored as file is already downloaded
        else:
            QMessageBox.critical(self, "Error", f"Update download failed: {error_msg}")

    def initUI(self):
        self.setWindowTitle(f"{T('WindowTitle', self.cfg.language)} v{self.VERSION}")
        self.resize(*self.cfg.window_size)
        self.setAcceptDrops(True)
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Status / Log timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.updateGeneralInfo)
        self.update_timer.start(1000) # Update every second
        
        # --- TAB 1: Main (Processing) ---
        self.tabMain = QWidget()
        self.tabs.addTab(self.tabMain, T("tabMain", self.cfg.language))
        tab1_layout = QVBoxLayout(self.tabMain)
        tab1_layout.setContentsMargins(10, 10, 10, 10)
        

        
        # Top Panel (Paths) - styled like Settings blocks
        # Top Panel (Paths) - styled like Settings blocks
        
        # Paths Block (Framed)
        frm_paths, paths_layout, self.lblPathsHeader = self.create_section_frame(T("grpPaths", self.cfg.language))
        tab1_layout.addWidget(frm_paths)
        
        # Combined Layout for Buttons + Output
        # [AddFiles] [AddFolder] [Clear] --space-- [Label] [Output] [...]
        
        # Buttons
        self.btnAddFiles = QPushButton(T("btnAddFiles", self.cfg.language))
        self.btnAddFiles.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        self.btnAddFiles.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnAddFiles.setStyleSheet("QPushButton { text-align: left; padding-left: 10px; }")
        self.btnAddFiles.clicked.connect(self.addFiles)
        
        self.btnAddFolder = QPushButton(T("btnAddFolder", self.cfg.language))
        self.btnAddFolder.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        self.btnAddFolder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnAddFolder.setStyleSheet("QPushButton { text-align: left; padding-left: 10px; }")
        self.btnAddFolder.clicked.connect(self.addFolder)
        
        self.btnClear = QPushButton(T("btnClear", self.cfg.language))
        self.btnClear.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton))
        self.btnClear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnClear.setStyleSheet("QPushButton { text-align: left; padding-left: 10px; }")
        self.btnClear.clicked.connect(self.clearList)
        
        paths_layout.addWidget(self.btnAddFiles)
        paths_layout.addWidget(self.btnAddFolder)
        paths_layout.addWidget(self.btnClear)
        
        # Space between buttons and output
        paths_layout.addSpacing(30)
        
        # Output Folder
        self.lblOutput = QLabel(T("lblOutput", self.cfg.language))
        self.txtOutput = QLineEdit()
        self.txtOutput.setReadOnly(True)
        self.txtOutput.setPlaceholderText(T("lblOutput", self.cfg.language))
        self.txtOutput.setText(self.cfg.output_folder)
        self.txtOutput.textChanged.connect(self.onOutputChanged)
        
        btnBrowseOutput = QToolButton()
        btnBrowseOutput.setText("...")
        btnBrowseOutput.clicked.connect(self.browseOutput)
        
        paths_layout.addWidget(self.lblOutput)
        paths_layout.addWidget(self.txtOutput)
        paths_layout.addWidget(btnBrowseOutput)
        
        # Ensure Output field expands
        paths_layout.setStretchFactor(self.txtOutput, 1)
        
        # Toolbar (old one removed, buttons moved into paths_layout)
        # tab1_layout.addLayout(toolbar_layout) # This line is removed
        
        # Header Info Widget (Corner of tabs)
        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 10, 0)
        header_layout.setSpacing(15)
        
        self.lblInfo = QLabel()
        self.lblInfo.setOpenExternalLinks(True)
        self.lblInfo.setStyleSheet("color: #888; font-weight: bold;")
        
        self.lblDATCount = QLabel("")
        self.lblDATCount.setStyleSheet("color: #4da6ff; font-weight: bold; border: 1px solid #333; border-radius: 4px; padding: 2px 8px; background-color: #1a1a1a;")
        
        header_layout.addWidget(self.lblInfo)
        header_layout.addWidget(self.lblDATCount)
        
        self.tabs.setCornerWidget(self.header_widget, Qt.Corner.TopRightCorner)
        self.updateDATCount()
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        # Column Widths
        h_header = self.table.horizontalHeader()
        h_header.setStyleSheet("font-weight: bold;")
        
        # Make all columns interactive (resizable)
        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h_header.setStretchLastSection(True)
        h_header.setMinimumSectionSize(50)  # Prevent columns from being too small
        
        # Default Column Widths
        self.table.setColumnWidth(0, 450) # File
        self.table.setColumnWidth(1, 60)  # Count
        self.table.setColumnWidth(2, 100) # Status
        self.table.setColumnWidth(3, 150) # Platform
        self.table.setColumnWidth(4, 80)  # Format
        self.table.setColumnWidth(5, 80)  # Start Size
        self.table.setColumnWidth(6, 80)  # End Size
        self.table.setColumnWidth(7, 80)  # Diff
        self.table.setColumnWidth(8, 120) # SHA1
        self.table.setColumnWidth(9, 120) # Serial
        
        # Restore saved widths
        if len(self.cfg.column_widths) == 10:
            for i, w in enumerate(self.cfg.column_widths):
                self.table.setColumnWidth(i, w)
        
        # Vertical Header
        v_header = self.table.verticalHeader()
        v_header.setFixedWidth(50)
        v_header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        v_header.setStyleSheet("font-weight: bold;")
        v_header.setDefaultSectionSize(45) # Increased row height

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.showContextMenu)
        self.table.cellChanged.connect(self.onCellChanged)
        
        # Add margins to table container
        table_container = QWidget()
        table_layout = QHBoxLayout(table_container)
        table_layout.setContentsMargins(5, 0, 5, 0)  # Left and right margins
        table_layout.addWidget(self.table)
        
        tab1_layout.addWidget(table_container)
        
        # File count label
        self.lblFileCount = QLabel("0 files")
        tab1_layout.addWidget(self.lblFileCount)
        
        
        # Log and Info Block Area
        log_info_layout = QHBoxLayout()
        
        # Log Block (on Main Tab) - Takes 2/3 width
        self.txtLog = QTextEdit()
        self.txtLog.setReadOnly(True)
        # Base style will be applied via updateLogStyle later
        self.txtLog.setMaximumHeight(200)
        log_info_layout.addWidget(self.txtLog, 2)
        
        # General Info Block - Takes 1/3 width
        frm_info, self.lblGeneralInfoHeader = self.create_general_info_block()
        frm_info.setMaximumHeight(200) 
        log_info_layout.addWidget(frm_info, 1)
        
        tab1_layout.addLayout(log_info_layout)
        
        # Action Panel
        action_layout = QHBoxLayout()
        self.btnStart = QPushButton(T("btnStart", self.cfg.language))
        self.btnStart.setFixedHeight(45)
        # Font size handled by theme now
        self.btnStart.setStyleSheet("font-weight: bold;") 
        self.btnStart.clicked.connect(lambda: self.startProcessing())
        
        self.btnStop = QPushButton(T("btnStop", self.cfg.language))
        self.btnStop.setFixedHeight(45)
        self.btnStop.setStyleSheet("font-weight: bold;")
        self.btnStop.setEnabled(False)
        self.btnStop.clicked.connect(self.stopProcessing)
        
        action_layout.addWidget(self.btnStart)
        action_layout.addWidget(self.btnStop)
        tab1_layout.addLayout(action_layout)
        
        self.initSettingsTab()

        # Status Bar
        self.statusBar = self.statusBar()
        self.statusLabel = QLabel(T("LogReady", self.cfg.language))
        self.statusBar.addWidget(self.statusLabel)
        
        self.progressBar = QProgressBar()
        self.progressBar.setVisible(False)
        self.progressBar.setFixedWidth(400)
        self.statusBar.addPermanentWidget(self.progressBar)
        
        # Events
        self.btnClear.clicked.connect(self.clearList)
        

        
        self.retranslateUi()
        
        self.updateLog(T("LogStarted", self.cfg.language))
        self.updateLog(T("LogReady", self.cfg.language))
        
        self.loadPresetsTable()
        self.updateLogStyle() # Apply initial log font settings

    def updateLogStyle(self):
        base_style = "background-color: #1e1e1e; color: #dcdcdc; font-family: Consolas, monospace;"
        
        # Stylesheet for QGroupBox to fix title alignment
        gb_style = """
        QGroupBox {
            border: 1px solid #555;
            border-radius: 5px;
            margin-top: 20px; /* Leave space for title */
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
            left: 10px;
            color: #00ffaa; /* Accent color text */
        }
        """
        self.setStyleSheet(self.styleSheet() + gb_style)

        if self.cfg.log_font_enabled:
            size = self.cfg.log_font_size
            self.txtLog.setStyleSheet(f"{base_style} font-size: {size}pt;")
        else:
            self.txtLog.setStyleSheet(base_style)
        
    def updateDATCount(self):
        dats_folder = os.path.join(get_app_dir(), "DATs")
        count = 0
        if os.path.exists(dats_folder):
            count = len([f for f in os.listdir(dats_folder) if f.lower().endswith('.dat') or f.lower().endswith('.zip')])
        
        txt = "DAT files: " if self.cfg.language == "EN" else "DAT-файлов: "
        self.lblDATCount.setText(f"{txt}{count}")
        
    def populateHunkSizes(self, combo, disk_type):
        combo.clear()
        if disk_type == "CD":
            # 2352 first
            combo.addItem("2352")
            # 1..428 * 2448
            for i in range(1, 429):
                val = i * 2448
                combo.addItem(str(val))
        elif disk_type == "DVD":
            # DVD: 1..512 * 2048
            for i in range(1, 513):
                val = i * 2048
                combo.addItem(str(val))
        self.align_combo_items(combo)

    def changeLanguage(self, index):
        if index == 1: self.cfg.language = "RU"
        else: self.cfg.language = "EN"
        self.retranslateUi()
        
    def toggleLargeFont(self, checked):
        self.cfg.large_font = checked
        self.cfg.save()
        self.applyTheme()
        
    def changeTheme(self, idx):
        self.cfg.theme = self.cmbTheme.currentText()
        self.cfg.save()
        self.applyTheme()

    def applyTheme(self):
        theme_data = next((t for t in THEMES if t["Name"] == self.cfg.theme), THEMES[0])
        
        # Determine base font size
        font_size = 13 if self.cfg.large_font else 9
        
        qss = get_qss(theme_data, font_size)
        self.setStyleSheet(qss)
        
        # Apply specific overrides for Log / Tables if needed
        # We need to update table font size too if global font changes?
        # The Style Sheet applies to QWidget, so tables should inherit font-size.
        # But we explicitly set row height, which might be too small for large font.
        
        if self.cfg.large_font:
             # Increase row heights for better visibility
             self.table.verticalHeader().setDefaultSectionSize(60)
             if hasattr(self, 'tblPresets'): self.tblPresets.verticalHeader().setDefaultSectionSize(60)
             if hasattr(self, 'tblOutputFolders'): self.tblOutputFolders.verticalHeader().setDefaultSectionSize(60)
        else:
             self.table.verticalHeader().setDefaultSectionSize(45)
             if hasattr(self, 'tblPresets'): self.tblPresets.verticalHeader().setDefaultSectionSize(45)
             if hasattr(self, 'tblOutputFolders'): self.tblOutputFolders.verticalHeader().setDefaultSectionSize(45)

        
        
        # Re-apply log font size if enabled, otherwise it uses theme default
        self.updateLogStyle()
        self.updateHeaderStyle(font_size)
        
        # Re-apply highlighting to current theme
        # self.updateControls() # This might be overkill / loop

    def updateHeaderStyle(self, base_font_size):
        header_size = base_font_size + 4
        style = f"QLabel#SectionHeader {{ font-weight: bold; font-size: {header_size}pt; color: #4da6ff; }}"
        self.setStyleSheet(self.styleSheet() + style)
        
    def create_general_info_block(self):
        frame = QFrame()
        frame.setObjectName("SettingsFrame") # Reuse settings frame style
        
        # Outer Layout
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(15, 15, 15, 15)
        outer.setSpacing(10)
        
        # Header
        lbl_header = QLabel(T("grpGeneralInfo", self.cfg.language))
        lbl_header.setObjectName("SectionHeader")
        outer.addWidget(lbl_header)
        
        # Separator (Horizontal)
        line_h = QFrame()
        line_h.setFrameShape(QFrame.Shape.HLine)
        line_h.setFrameShadow(QFrame.Shadow.Sunken)
        line_h.setStyleSheet("background-color: #444; margin-bottom: 5px;")
        outer.addWidget(line_h)
        
        # Main Content Layout (Horizontal Split)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Helper for bold title labels
        def bold_lbl(text):
            l = QLabel(text)
            # Increased font size by 2pt
            base_size = self.font().pointSize()
            if base_size <= 0: base_size = 10
            new_size = base_size + 2
            
            l.setStyleSheet(f"font-weight: bold; color: #aaa; font-size: {new_size}pt;")
            l.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return l

        # Style for values
        base_size = self.font().pointSize()
        if base_size <= 0: base_size = 10
        new_size = base_size + 2
        
        val_style = f"font-weight: bold; color: #dcdcdc; padding-left: 10px; font-size: {new_size}pt;"

        # --- Left Block: Sizes ---
        grid_left = QGridLayout()
        grid_left.setSpacing(8)
        
        self.lblTotalStartSize = QLabel("0 B")
        self.lblTotalEndSize = QLabel("0 B")
        self.lblTotalDiff = QLabel("0 B")
        
        for l in [self.lblTotalStartSize, self.lblTotalEndSize, self.lblTotalDiff]:
            l.setStyleSheet(val_style)
            
        grid_left.addWidget(bold_lbl(T("lblTotalStartSize", self.cfg.language)), 0, 0)
        grid_left.addWidget(self.lblTotalStartSize, 0, 1)
        grid_left.addWidget(bold_lbl(T("lblTotalEndSize", self.cfg.language)), 1, 0)
        grid_left.addWidget(self.lblTotalEndSize, 1, 1)
        grid_left.addWidget(bold_lbl(T("lblTotalDiff", self.cfg.language)), 2, 0)
        grid_left.addWidget(self.lblTotalDiff, 2, 1)

        content_layout.addLayout(grid_left, 1)
        
        # Separator (Vertical)
        line_v = QFrame()
        line_v.setFrameShape(QFrame.Shape.VLine)
        line_v.setFrameShadow(QFrame.Shadow.Sunken)
        line_v.setStyleSheet("background-color: #444;")
        content_layout.addWidget(line_v)
        
        # --- Right Block: Tasks ---
        grid_right = QGridLayout()
        grid_right.setSpacing(8)
        
        self.lblTotalTasks = QLabel("0")
        self.lblFinishedTasks = QLabel("0")
        self.lblInProgressTasks = QLabel("0")
        
        for l in [self.lblTotalTasks, self.lblFinishedTasks, self.lblInProgressTasks]:
            l.setStyleSheet(val_style)
            
        grid_right.addWidget(bold_lbl(T("lblTotalTasks", self.cfg.language)), 0, 0)
        grid_right.addWidget(self.lblTotalTasks, 0, 1)
        grid_right.addWidget(bold_lbl(T("lblFinishedTasks", self.cfg.language)), 1, 0)
        grid_right.addWidget(self.lblFinishedTasks, 1, 1)
        grid_right.addWidget(bold_lbl(T("lblInProgressTasks", self.cfg.language)), 2, 0)
        grid_right.addWidget(self.lblInProgressTasks, 2, 1)
        
        content_layout.addLayout(grid_right, 1)
        
        outer.addLayout(content_layout)
        outer.addStretch()
        
        return frame, lbl_header

    def updateGeneralInfo(self):
        total_start = 0
        total_end = 0
        
        tasks_total = 0
        tasks_done = 0
        tasks_skipped = 0
        
        for row in range(self.table.rowCount()):
            # Status (Col 2)
            item_status = self.table.item(row, 2)
            status_text = item_status.text() if item_status else ""
            
            # Start Size (Col 5) - count for all files first
            item_start = self.table.item(row, 5)
            start_size = 0
            if item_start:
                try:
                    start_size = int(item_start.data(Qt.ItemDataRole.UserRole) or 0)
                    if start_size <= 0:
                        start_size = self._parse_size_text(item_start.text())
                except: 
                    start_size = self._parse_size_text(item_start.text())
            
            # Check if skipped - exclude from totals
            if status_text == T("StatusSkipped", self.cfg.language):
                tasks_skipped += 1
                continue
            
            # Add to totals only for non-skipped files
            total_start += start_size
            tasks_total += 1
            
            # End Size (Col 6)
            item_end = self.table.item(row, 6)
            if item_end:
                 try:
                     total_end += int(item_end.data(Qt.ItemDataRole.UserRole) or 0)
                 except: pass

            # Count done tasks
            if status_text == T("StatusDone", self.cfg.language):
                tasks_done += 1
        
        # Calculate remaining tasks (not done yet)
        tasks_remaining = tasks_total - tasks_done
                
        # Diff - handle cases where end size is 0 (not yet processed)
        if total_end > 0:
            diff = total_start - total_end
            diff_text = get_readable_size(abs(diff))
            if diff < 0:
                diff_text = "+" + diff_text
            else:
                diff_text = "-" + diff_text
        else:
            diff_text = "-"
        
        self.lblTotalStartSize.setText(get_readable_size(total_start))
        self.lblTotalEndSize.setText(get_readable_size(total_end) if total_end > 0 else "-")
        self.lblTotalDiff.setText(diff_text)
        
        self.lblTotalTasks.setText(str(tasks_total))
        self.lblFinishedTasks.setText(str(tasks_done))
        self.lblInProgressTasks.setText(str(tasks_remaining))

    def create_framed_widget(self, widget, fixed_width=None, min_height=60):
        frame = QFrame()
        frame.setObjectName("SettingsFrame")
        # Styling now handled by theme system via QFrame#SettingsFrame selector
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(5, 5, 5, 5)
        lay.addWidget(widget)
        if fixed_width:
            frame.setMaximumWidth(fixed_width)
            frame.setMinimumWidth(180)
        if min_height and min_height > 0:
            frame.setMinimumHeight(min_height)
        return frame
        
    def create_wrapping_checkbox(self, text, checked, callback=None):
        """Creates a Layout with [Checkbox] [WrappedLabel]"""
        wid = QWidget()
        lay = QHBoxLayout(wid)
        lay.setContentsMargins(0,0,0,0)
        lay.setSpacing(5)
        
        chk = QCheckBox()
        chk.setChecked(checked)
        if callback:
            chk.toggled.connect(callback)
            
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        # Optional: Click label to toggle
        # We need a custom label or event filter, but simple way is subclass/hack
        # For now just display. User can click checkbox. 
        # Actually standard usage expects clicking text to toggle.
        # Let's try to make label transparent to mouse events? No, we need it to accept click and trigger chk.
        # Simple fix:
        def mousePressEvent(e):
            chk.toggle()
        lbl.mousePressEvent = mousePressEvent
        
        lay.addWidget(chk)
        lay.addWidget(lbl, 1) # stretch
        lay.setAlignment(chk, Qt.AlignmentFlag.AlignVCenter) # Align checkbox to center of text block
        
        # Store label ref for retranslateUi
        chk.wrapper_label = lbl
        
        return wid, chk
        
    def align_combo_items(self, combo):
        for i in range(combo.count()):
            combo.setItemData(i, Qt.AlignmentFlag.AlignCenter, Qt.ItemDataRole.TextAlignmentRole)

    def setup_centered_combo(self, combo, editable=False):
        combo.setEditable(True)
        combo.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)  # Don't add typed values to list
        # Enable autocomplete with partial matching
        completer = combo.completer()
        if completer:
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.align_combo_items(combo)

    def create_section_frame(self, title, layout_type=QHBoxLayout):
        """Creates a frame with a title header and a content layout."""
        frame = QFrame()
        frame.setObjectName("SettingsFrame") # Reusing the frame style
        
        # Outer layout for Title + Content
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(10)
        
        # Title
        lbl = QLabel(title)
        lbl.setObjectName("SectionHeader")
        # Base style set here, but size controlled by stylesheet in applyTheme
        # lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #4da6ff;") 
        outer.addWidget(lbl)
        
        # Content Layout
        content = layout_type()
        content.setSpacing(15)
        outer.addLayout(content)
        
        return frame, content, lbl

    def initSettingsTab(self):
        # --- TAB 2: Settings ---
        self.tabSettings = QWidget()
        self.tabs.addTab(self.tabSettings, T("tabSettings", self.cfg.language))
        
        main_layout = QVBoxLayout(self.tabSettings)
        # Scroll Area for Settings because it might get tall
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Standard width for option blocks inputs
        # Standard width for option blocks inputs
        BLOCK_WIDTH = 380
        
        # --- 0. Languages & Theme (Row) ---
        frm_theme, row_theme, self.lblThemeSettings = self.create_section_frame(T("grpTheme", self.cfg.language) + " / " + T("grpLanguage", self.cfg.language))
        layout.addWidget(frm_theme)
        
        # Theme
        wid_theme = QWidget()
        lay_theme = QHBoxLayout(wid_theme)
        lay_theme.setContentsMargins(0,0,0,0)
        self.lblTheme = QLabel(T("lblTheme", self.cfg.language))
        self.cmbTheme = QComboBox()
        self.cmbTheme.setMinimumWidth(200)
        theme_names = [t["Name"] for t in THEMES]
        self.cmbTheme.addItems(theme_names)
        self.setup_centered_combo(self.cmbTheme)
        self.cmbTheme.setCurrentText(self.cfg.theme)
        self.cmbTheme.currentIndexChanged.connect(self.changeTheme)
        lay_theme.addWidget(self.lblTheme)
        lay_theme.addWidget(self.cmbTheme)
        row_theme.addWidget(self.create_framed_widget(wid_theme, BLOCK_WIDTH))
        
        # Language
        wid_lang = QWidget()
        lay_lang = QHBoxLayout(wid_lang)
        lay_lang.setContentsMargins(0,0,0,0)
        self.lblLanguage = QLabel(T("lblLanguage", self.cfg.language))
        self.cmbLanguage = QComboBox()
        self.cmbLanguage.setMinimumWidth(200)
        self.cmbLanguage.addItems(["English", "Русский"])
        self.setup_centered_combo(self.cmbLanguage)
        if self.cfg.language == "RU": self.cmbLanguage.setCurrentIndex(1)
        self.cmbLanguage.currentIndexChanged.connect(self.changeLanguage)
        lay_lang.addWidget(self.lblLanguage)
        lay_lang.addWidget(self.cmbLanguage)
        row_theme.addWidget(self.create_framed_widget(wid_lang, BLOCK_WIDTH))
        
        # Large Font Checkbox
        # Large Font Checkbox
        w_large, self.chkLargeFont = self.create_wrapping_checkbox(T("chkLargeFont", self.cfg.language), self.cfg.large_font, self.toggleLargeFont)
        row_theme.addWidget(self.create_framed_widget(w_large, BLOCK_WIDTH))
        
        row_theme.addStretch()
        
        
        # --- 1. Files & Recognition (Row) ---
        frm_files, row_files, self.lblFileOps = self.create_section_frame(T("grpFileOps", self.cfg.language))
        layout.addWidget(frm_files)
        
        w_overwrite, self.chkOverwrite = self.create_wrapping_checkbox(T("chkOverwrite", self.cfg.language), self.cfg.force_overwrite)
        row_files.addWidget(self.create_framed_widget(w_overwrite, BLOCK_WIDTH))
        
        w_recog, self.chkRecognition = self.create_wrapping_checkbox(T("chkRecognition", self.cfg.language), self.cfg.platform_recognition)
        row_files.addWidget(self.create_framed_widget(w_recog, BLOCK_WIDTH))
        
        w_sub, self.chkExtractSubfolders = self.create_wrapping_checkbox(T("chkExtractSubfolders", self.cfg.language), self.cfg.extract_subfolders, self.onExtractSubfoldersToggled)
        row_files.addWidget(self.create_framed_widget(w_sub, BLOCK_WIDTH))
        
        w_del, self.chkDeleteSource = self.create_wrapping_checkbox(T("chkDeleteSource", self.cfg.language), self.cfg.delete_source, self.onDeleteSourceToggled)
        row_files.addWidget(self.create_framed_widget(w_del, BLOCK_WIDTH))
        
        row_files.addStretch()
        
        
        # --- 2. Compression & Logic (Row) ---
        frm_comp, row_comp, self.lblCompSettings = self.create_section_frame(T("grpCompressionSettings", self.cfg.language))
        layout.addWidget(frm_comp)

        # AetherSX2
        # AetherSX2
        w_aether, self.chkAetherSX2 = self.create_wrapping_checkbox(T("chkAetherSX2", self.cfg.language), self.cfg.preset_aethersx2, self.onAetherSX2Toggled)
        row_comp.addWidget(self.create_framed_widget(w_aether, BLOCK_WIDTH))
        
        # Threads
        wid_threads = QWidget()
        lay_threads = QHBoxLayout(wid_threads)
        lay_threads.setContentsMargins(0,0,0,0)
        self.lblThreads = QLabel(T("lblThreads", self.cfg.language))
        self.cmbThreads = QComboBox()
        self.cmbThreads.addItem("Auto")
        self.cmbThreads.addItems([str(i) for i in range(1, os.cpu_count() + 1)])
        self.setup_centered_combo(self.cmbThreads)
        if self.cfg.threads == 0: self.cmbThreads.setCurrentText("Auto")
        else: self.cmbThreads.setCurrentText(str(self.cfg.threads))
        lay_threads.addWidget(self.lblThreads)
        lay_threads.addWidget(self.cmbThreads)
        row_comp.addWidget(self.create_framed_widget(wid_threads, BLOCK_WIDTH))
        
        # Algo
        wid_algo = QWidget()
        lay_algo = QHBoxLayout(wid_algo)
        lay_algo.setContentsMargins(0,0,0,0)
        self.lblCompression = QLabel(T("lblCompression", self.cfg.language))
        self.cmbCompression = QComboBox()
        self.cmbCompression.setMinimumWidth(120)
        self.cmbCompression.addItems(["lzma", "zlib"])
        self.setup_centered_combo(self.cmbCompression)
        self.cmbCompression.setCurrentText(self.cfg.compression)
        lay_algo.addWidget(self.lblCompression)
        lay_algo.addWidget(self.cmbCompression)
        row_comp.addWidget(self.create_framed_widget(wid_algo, BLOCK_WIDTH))
        
        row_comp.addStretch()
        
        
        # --- 3. Hunk Sizes (Row) ---
        frm_hunks, row_hunk, self.lblHunkSettings = self.create_section_frame(T("grpHunkSettings", self.cfg.language))
        layout.addWidget(frm_hunks)
        
        # CD
        wid_cd = QWidget()
        lay_cd = QHBoxLayout(wid_cd)
        lay_cd.setContentsMargins(0,0,0,0)
        self.lblHunkCD = QLabel(T("lblHunkCD", self.cfg.language))
        self.cmbHunkCD = QComboBox()
        self.cmbHunkCD.setMinimumWidth(120)
        self.cmbHunkCD.setEditable(True)
        self.populateHunkSizes(self.cmbHunkCD, "CD")
        self.setup_centered_combo(self.cmbHunkCD, editable=True)
        self.cmbHunkCD.setCurrentText(str(self.cfg.hunk_cd))
        lay_cd.addWidget(self.lblHunkCD)
        lay_cd.addWidget(self.cmbHunkCD)
        row_hunk.addWidget(self.create_framed_widget(wid_cd, BLOCK_WIDTH))
        
        # DVD
        wid_dvd = QWidget()
        lay_dvd = QHBoxLayout(wid_dvd)
        lay_dvd.setContentsMargins(0,0,0,0)
        self.lblHunkDVD = QLabel(T("lblHunkDVD", self.cfg.language))
        self.cmbHunkDVD = QComboBox()
        self.cmbHunkDVD.setMinimumWidth(120)
        self.cmbHunkDVD.setEditable(True)
        self.populateHunkSizes(self.cmbHunkDVD, "DVD")
        self.setup_centered_combo(self.cmbHunkDVD, editable=True)
        self.cmbHunkDVD.setCurrentText(str(self.cfg.hunk_dvd))
        lay_dvd.addWidget(self.lblHunkDVD)
        lay_dvd.addWidget(self.cmbHunkDVD)
        row_hunk.addWidget(self.create_framed_widget(wid_dvd, BLOCK_WIDTH))
        
        row_hunk.addStretch()

        
        # --- 4. Tray & Updates (Row) ---
        frm_tray, row_tray, self.lblTraySettings = self.create_section_frame(T("grpTray", self.cfg.language) + " / " + T("grpUpdates", self.cfg.language))
        layout.addWidget(frm_tray)
        
        w_min, self.chkMinimizeTray = self.create_wrapping_checkbox(T("chkMinimizeTray", self.cfg.language), self.cfg.minimize_to_tray, self.onMinimizeTrayToggled)
        row_tray.addWidget(self.create_framed_widget(w_min, BLOCK_WIDTH))
        
        w_close, self.chkCloseTray = self.create_wrapping_checkbox(T("chkCloseTray", self.cfg.language), self.cfg.close_to_tray, self.onCloseTrayToggled)
        row_tray.addWidget(self.create_framed_widget(w_close, BLOCK_WIDTH))
        
        w_auto, self.chkAutoUpdate = self.create_wrapping_checkbox(T("chkAutoUpdate", self.cfg.language), self.cfg.auto_update)
        row_tray.addWidget(self.create_framed_widget(w_auto, BLOCK_WIDTH))
        
        row_tray.addStretch()
        
        
        # --- 5. Notifications (Reordered: Log -> Text -> Sound) ---
        frm_notif, row_notif, self.lblNotifSettings = self.create_section_frame(T("grpNotification", self.cfg.language))
        layout.addWidget(frm_notif)
        
        # 1. Log Font (Moved here)
        # 1. Log Font (Moved here)
        w_chklog, self.chkLogFont = self.create_wrapping_checkbox(T("chkLogFont", self.cfg.language), self.cfg.log_font_enabled, self.onLogFontEnabledToggled)
        
        self.spnLogFont = QSpinBox()
        self.spnLogFont.setRange(8, 24)
        self.spnLogFont.setValue(self.cfg.log_font_size)
        self.spnLogFont.setEnabled(self.cfg.log_font_enabled)
        self.spnLogFont.valueChanged.connect(self.onLogFontChanged)
        self.spnLogFont.setFixedWidth(70) 
        self.spnLogFont.setStyleSheet("QSpinBox::up-button, QSpinBox::down-button { height: 10px; }")
        
        wid_log = QWidget()
        lay_log = QHBoxLayout(wid_log)
        lay_log.setContentsMargins(0,0,0,0)
        lay_log.addWidget(w_chklog, 1) # Give it stretch
        lay_log.addWidget(self.spnLogFont)
        row_notif.addWidget(self.create_framed_widget(wid_log, BLOCK_WIDTH))
        
        # 2. Text Notification
        # 2. Text Notification
        w_txt, self.chkNotifyText = self.create_wrapping_checkbox(T("chkNotifyText", self.cfg.language), self.cfg.notify_text)
        row_notif.addWidget(self.create_framed_widget(w_txt, BLOCK_WIDTH))
        
        # 3. Sound Notification + Custom Picker
        wid_sound = QWidget()
        lay_sound = QHBoxLayout(wid_sound)
        lay_sound.setContentsMargins(0,0,0,0)
        
        w_snd, self.chkNotifySound = self.create_wrapping_checkbox(T("chkNotifySound", self.cfg.language), self.cfg.notify_sound)
        
        self.btnSelectSound = QToolButton()
        self.btnSelectSound.setText("...")
        self.btnSelectSound.setToolTip("Select custom notification.wav")
        self.btnSelectSound.clicked.connect(self.selectCustomSound)
        
        lay_sound.addWidget(w_snd, 1) # stretch
        lay_sound.addWidget(self.btnSelectSound)
        
        row_notif.addWidget(self.create_framed_widget(wid_sound, BLOCK_WIDTH))
        
        row_notif.addStretch()
        
        # Spacer
        layout.addSpacing(20)
        
        # --- 7. Platform Presets (Collapsible) ---
        self.boxPresets = CollapsibleBox(T("grpPresets", self.cfg.language))
        
        # Presets Content
        presets_widget = QWidget()
        p_layout = QVBoxLayout(presets_widget)
        p_layout.setContentsMargins(0,0,0,0) 
        
        p_toolbar = QHBoxLayout()
        self.btnAddPreset = QPushButton(T("btnAddPreset", self.cfg.language))
        self.btnAddPreset.setFixedWidth(120)
        self.btnAddPreset.clicked.connect(lambda: self.addPresetRow())
        
        self.btnDelPreset = QPushButton(T("btnDelPreset", self.cfg.language))
        self.btnDelPreset.setFixedWidth(120)
        self.btnDelPreset.clicked.connect(self.deletePresetRow)
        
        p_toolbar.addWidget(self.btnAddPreset)
        p_toolbar.addWidget(self.btnDelPreset)
        p_toolbar.addStretch()
        p_layout.addLayout(p_toolbar)
        
        self.tblPresets = QTableWidget()
        self.tblPresets.setColumnCount(6)
        self.tblPresets.setHorizontalHeaderLabels([
            T("colEnabled", self.cfg.language),
            T("colPlatform", self.cfg.language),
            T("colAlgo", self.cfg.language),
            T("colHunkCD", self.cfg.language),
            T("colHunkDVD", self.cfg.language),
            T("colComment", self.cfg.language)
        ])
        
        # Ensure row numbering is visible and centered
        self.tblPresets.verticalHeader().setVisible(True)
        self.tblPresets.verticalHeader().setFixedWidth(35)
        self.tblPresets.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tblPresets.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # Fixed Widths for Presets
        self.tblPresets.setColumnWidth(1, 300) # Platform
        self.tblPresets.setColumnWidth(2, 150) # Algo
        self.tblPresets.setColumnWidth(3, 150) # CD
        self.tblPresets.setColumnWidth(4, 150) # DVD
        self.tblPresets.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch) # Comment
        
        self.tblPresets.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tblPresets.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tblPresets.verticalHeader().setDefaultSectionSize(45)  # Increased row height
        self.tblPresets.itemChanged.connect(self.onPresetItemChanged)
        
        # Context Menu & Shortcut
        self.tblPresets.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tblPresets.customContextMenuRequested.connect(lambda pos: self.onTableContextMenu(pos, self.tblPresets))
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self.tblPresets, activated=self.deletePresetRow)
        
        p_layout.addWidget(self.tblPresets)
        
        self.boxPresets.setContent(presets_widget)
        layout.addWidget(self.create_framed_widget(self.boxPresets, min_height=0)) # Frame the box, no min height
        
        layout.addSpacing(10)

        # --- 8. Output Folders (Collapsible) ---
        self.boxOutputFolders = CollapsibleBox(T("grpOutputFolders", self.cfg.language))
        
        out_widget = QWidget()
        o_layout = QVBoxLayout(out_widget)
        o_layout.setContentsMargins(0,0,0,0)
        
        o_toolbar = QHBoxLayout()
        self.btnAddOutput = QPushButton(T("btnAddPreset", self.cfg.language))
        self.btnAddOutput.setFixedWidth(120)
        self.btnAddOutput.clicked.connect(lambda: self.addOutputFolderRow())
        
        self.btnDelOutput = QPushButton(T("btnDelPreset", self.cfg.language))
        self.btnDelOutput.setFixedWidth(120)
        self.btnDelOutput.clicked.connect(self.deleteOutputFolderRow)
        
        o_toolbar.addWidget(self.btnAddOutput)
        o_toolbar.addWidget(self.btnDelOutput)
        o_toolbar.addStretch()
        o_layout.addLayout(o_toolbar)
        
        self.tblOutputFolders = QTableWidget()
        self.tblOutputFolders.setColumnCount(3) # Removed empty col
        self.tblOutputFolders.setHorizontalHeaderLabels([
            T("colEnabled", self.cfg.language),
            T("colPlatform", self.cfg.language),
            T("colOutput", self.cfg.language)
        ])
        
        # Ensure row numbering is visible and centered
        self.tblOutputFolders.verticalHeader().setVisible(True)
        self.tblOutputFolders.verticalHeader().setFixedWidth(35)
        self.tblOutputFolders.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tblOutputFolders.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.tblOutputFolders.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tblOutputFolders.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        self.tblOutputFolders.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tblOutputFolders.verticalHeader().setDefaultSectionSize(45)  # Increased row height
        
        # Context Menu & Shortcut
        self.tblOutputFolders.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tblOutputFolders.customContextMenuRequested.connect(lambda pos: self.onTableContextMenu(pos, self.tblOutputFolders))
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self.tblOutputFolders, activated=self.deleteOutputFolderRow)
        
        o_layout.addWidget(self.tblOutputFolders)
        
        self.boxOutputFolders.setContent(out_widget)
        layout.addWidget(self.create_framed_widget(self.boxOutputFolders, min_height=0)) # Frame the box, no min height
        
        layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # Initial Load
        self.loadOutputFoldersTable()
        if hasattr(self, 'loadPresetsTable'): self.loadPresetsTable()



    def selectCustomSound(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Notification Sound", "", "WAV Files (*.wav)")
        if file_path:
            try:
                dest = os.path.join(get_app_dir(), "notification.wav")
                import shutil
                shutil.copy2(file_path, dest)
                QMessageBox.information(self, "Success", "Custom notification sound updated!")
                if self.chkNotifySound.isChecked():
                     # Optional: Play it to confirm?
                     pass
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to update sound: {e}")

    def onTableContextMenu(self, pos, table):
        menu = QMenu(self)
        delete_action = menu.addAction(T("btnDelPreset", self.cfg.language))
        
        # Map table to delete function
        handler = None
        if table == self.tblPresets:
            handler = self.deletePresetRow
        elif table == self.tblOutputFolders:
             handler = self.deleteOutputFolderRow
             
        if handler:
            delete_action.triggered.connect(handler)
            menu.exec(table.mapToGlobal(pos))



    def loadOutputFoldersTable(self):
        self.loading_output = True 
        self.tblOutputFolders.setRowCount(0)
        
        data_list = self.cfg.platform_output_folders
        for data in data_list:
            self.addOutputFolderRow(data)
            
        self.loading_output = False
        
    def addOutputFolderRow(self, data=None):
        self.loading_output = True
        row = self.tblOutputFolders.rowCount()
        self.tblOutputFolders.insertRow(row)
        
        # Default Data
        enabled = data.get("enabled", True) if data else True
        platform = data.get("platform", "") if data else ""
        path = data.get("path", "") if data else ""
        
        # 0: Enabled (Center Checkbox)
        chk_w = QWidget()
        chk_l = QHBoxLayout(chk_w)
        chk_l.setContentsMargins(0,0,0,0)
        chk_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chk = QCheckBox()
        chk.setChecked(enabled)
        chk.toggled.connect(lambda: self.saveOutputFoldersFromTable())
        chk_l.addWidget(chk)
        self.tblOutputFolders.setCellWidget(row, 0, chk_w)
        
        # 1: Platform (Combo)
        cmb = QComboBox()
        cmb.setEditable(True)
        cmb.lineEdit().setAlignment(Qt.AlignmentFlag.AlignLeft)
        dats_folder = os.path.join(get_app_dir(), "DATs")
        plats = get_all_platforms(dats_folder)
        cmb.addItems(plats)
        cmb.setCurrentText(platform)
        cmb.currentIndexChanged.connect(lambda: self.saveOutputFoldersFromTable())
        cmb.lineEdit().editingFinished.connect(lambda: self.saveOutputFoldersFromTable())
        self.tblOutputFolders.setCellWidget(row, 1, cmb)
        
        # 2: Path + Browse (Composite)
        path_widget = QWidget()
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(2)
        
        txt = DropLineEdit()
        txt.setText(path)
        txt.textChanged.connect(lambda: self.saveOutputFoldersFromTable())
        path_layout.addWidget(txt)
        
        btn = QPushButton("...")
        btn.setFixedWidth(40)
        btn.clicked.connect(lambda _, r=row: self.browseRowPath(r))
        path_layout.addWidget(btn)
        
        self.tblOutputFolders.setCellWidget(row, 2, path_widget)
        
        self.loading_output = False
        if not data: self.saveOutputFoldersFromTable()

    def browseRowPath(self, row):
        folder = QFileDialog.getExistingDirectory(self, T("colOutput", self.cfg.language))
        if folder:
            w_path = self.tblOutputFolders.cellWidget(row, 2)
            if w_path:
                txt = w_path.findChild(DropLineEdit)
                if txt:
                    txt.setText(folder) # Triggers save

    def deleteOutputFolderRow(self):
        row = self.tblOutputFolders.currentRow()
        if row >= 0:
            self.tblOutputFolders.removeRow(row)
            self.saveOutputFoldersFromTable()

    def saveOutputFoldersFromTable(self):
        if getattr(self, "loading_output", False): return
        
        out_list = []
        for row in range(self.tblOutputFolders.rowCount()):
            # Enabled
            w_chk = self.tblOutputFolders.cellWidget(row, 0)
            enabled = True
            if w_chk:
                chk = w_chk.findChild(QCheckBox)
                if chk: enabled = chk.isChecked()
                
            # Platform
            w_cmb = self.tblOutputFolders.cellWidget(row, 1)
            platform = w_cmb.currentText() if w_cmb else ""
            
            # Path
            w_path = self.tblOutputFolders.cellWidget(row, 2)
            path = ""
            if w_path:
                txt = w_path.findChild(DropLineEdit)
                path = txt.text() if txt else ""
            
            if platform or path:
                out_list.append({
                    "enabled": enabled,
                    "platform": platform,
                    "path": path
                })
        
        self.cfg.platform_output_folders = out_list
        self.cfg.save()

    def retranslateUi(self):
        lang = self.cfg.language
        self.setWindowTitle(f"{T('WindowTitle', lang)} v{self.VERSION}")
        self.tabs.setTabText(0, T("tabMain", lang))
        self.tabs.setTabText(1, T("tabSettings", lang))
        
        self.lblPathsHeader.setText(T("grpPaths", lang))
        self.lblOutput.setText(T("lblOutput", lang))
        self.btnAddFiles.setText(T("btnAddFiles", lang))
        self.btnAddFolder.setText(T("btnAddFolder", lang))
        self.btnClear.setText(T("btnClear", lang))
        
        headers = [
            T("colFile", lang), T("colCount", lang), T("colStatus", lang), T("colPlatform", lang),
            T("colFormat", lang), T("colStartSize", lang), T("colEndSize", lang), T("colDiff", lang),
            T("colSHA1", lang), T("colSerial", lang)
        ]
        self.table.setHorizontalHeaderLabels(headers)
        
        self.btnStart.setText(T("btnStart", lang))
        self.btnStop.setText(T("btnStop", lang))
        
        # Settings Tab Headers
        self.lblFileOps.setText(T("grpFileOps", lang))
        self.lblCompSettings.setText(T("grpCompressionSettings", lang))
        self.lblHunkSettings.setText(T("grpHunkSettings", lang))
        self.lblTraySettings.setText(T("grpTray", lang) + " / " + T("grpUpdates", lang))
        self.lblNotifSettings.setText(T("grpNotification", lang))
        self.lblThemeSettings.setText(T("grpTheme", lang) + " / " + T("grpLanguage", lang))
        
        self.lblThemeSettings.setText(T("grpTheme", lang) + " / " + T("grpLanguage", lang))
        
        # Helper to set checkbox text (handles wrapped labels)
        def set_chk_text(chk, key):
            txt = T(key, lang)
            if hasattr(chk, 'wrapper_label'):
                chk.wrapper_label.setText(txt)
                chk.setText("")
            else:
                chk.setText(txt)

        set_chk_text(self.chkOverwrite, "chkOverwrite")
        set_chk_text(self.chkRecognition, "chkRecognition")
        set_chk_text(self.chkExtractSubfolders, "chkExtractSubfolders")
        set_chk_text(self.chkDeleteSource, "chkDeleteSource")
        
        set_chk_text(self.chkAetherSX2, "chkAetherSX2")
        self.lblThreads.setText(T("lblThreads", lang))
        self.lblCompression.setText(T("lblCompression", lang))
        
        self.lblHunkCD.setText(T("lblHunkCD", lang))
        self.lblHunkDVD.setText(T("lblHunkDVD", lang))
        
        set_chk_text(self.chkNotifyText, "chkNotifyText")
        set_chk_text(self.chkNotifySound, "chkNotifySound")
        set_chk_text(self.chkLogFont, "chkLogFont")
        
        set_chk_text(self.chkMinimizeTray, "chkMinimizeTray")
        set_chk_text(self.chkCloseTray, "chkCloseTray")
        set_chk_text(self.chkAutoUpdate, "chkAutoUpdate")
        
        set_chk_text(self.chkLargeFont, "chkLargeFont")
        
        self.lblLanguage.setText(T("lblLanguage", lang))
        self.lblTheme.setText(T("lblTheme", lang))

        # Checkboxes inside Collapsible Boxes? 
        # Actually 'grpPresets' logic was used for title, but now we use CollapsibleBox.
        self.boxPresets.lbl_title.setText(T("grpPresets", lang))
        self.boxPresets.btn_expand.setText(T("btnExpand", lang) if not self.boxPresets.btn_expand.isChecked() else T("btnCollapse", lang))
        
        self.btnAddPreset.setText(T("btnAddPreset", lang))
        self.btnDelPreset.setText(T("btnDelPreset", lang))
        
        self.tblPresets.setHorizontalHeaderLabels([
            T("colEnabled", lang),
            T("colPlatform", lang),
            T("colAlgo", lang),
            T("colHunkCD", lang),
            T("colHunkDVD", lang),
            T("colComment", lang)
        ])
        self.updateDATCount()
        
        self.initMenuBar()

    def initMenuBar(self):
        menubar = self.menuBar()
        menubar.clear()
        
        # Style: Bold text for Menu Bar items and Menu Dropdowns
        # Note: We need to respect the theme colors, so we just add font-weight.
        # But applyTheme overwrites global stylesheet. 
        # So we should probably set this in applyTheme or add to specific widget.
        # Let's set a specific object name or just styling here.
        # However, applyTheme on QMainWindow will propagate font-size.
        menubar.setStyleSheet("QMenuBar { font-weight: bold; } QMenu { font-weight: bold; }")
        
        # Tools Menu
        toolsMenu = menubar.addMenu(T("menuTools", self.cfg.language))
        
        actDownloadDATs = QAction(T("btnDownloadDATs", self.cfg.language), self)
        actDownloadDATs.triggered.connect(self.downloadDATs)
        toolsMenu.addAction(actDownloadDATs)
        
        actDeleteDATs = QAction(T("btnDeleteDATs", self.cfg.language), self)
        actDeleteDATs.triggered.connect(self.deleteDATs)
        toolsMenu.addAction(actDeleteDATs)
        
        toolsMenu.addSeparator()
        
        actClearCache = QAction(T("btnClearCache", self.cfg.language), self)
        actClearCache.triggered.connect(self.clearCache)
        toolsMenu.addAction(actClearCache)


    def onAetherSX2Toggled(self, checked):
        LOCKED_STYLE = "background-color: #502020; color: #e0e0e0;" if self.cfg.theme != "Platinum Light" else "background-color: #ffcccc; color: #000000;"
        style = LOCKED_STYLE if checked else ""
        
        if checked:
            # Save current settings before applying preset
            self.saved_settings = {
                "compression": self.cmbCompression.currentText(),
                "hunk_cd": self.cmbHunkCD.currentText(),
                "hunk_dvd": self.cmbHunkDVD.currentText()
            }
            
            idx = self.cmbCompression.findText("zlib") 
            if idx != -1: self.cmbCompression.setCurrentIndex(idx)
            
            self.cmbHunkCD.setCurrentText("4896")
            self.cmbHunkDVD.setCurrentText("4096")
            
            self.cmbCompression.setEnabled(False)
            self.cmbHunkCD.setEnabled(False)
            self.cmbHunkDVD.setEnabled(False)
            
            self.cmbCompression.setStyleSheet(style)
            self.cmbHunkCD.setStyleSheet(style)
            self.cmbHunkDVD.setStyleSheet(style)
        else:
            # Restore settings if available
            if self.saved_settings:
                self.cmbCompression.setCurrentText(self.saved_settings.get("compression", "lzma"))
                self.cmbHunkCD.setCurrentText(self.saved_settings.get("hunk_cd", "2352"))
                self.cmbHunkDVD.setCurrentText(self.saved_settings.get("hunk_dvd", "2048"))
            
            self.cmbCompression.setEnabled(True)
            self.cmbHunkCD.setEnabled(True)
            self.cmbHunkDVD.setEnabled(True)
            self.cmbCompression.setStyleSheet("")
            self.cmbHunkCD.setStyleSheet("")
            self.cmbHunkDVD.setStyleSheet("")
            
    def updateControls(self):
        # We don't want to save/restore on startup, just apply state?
        # Actually initial state is loaded from cfg. 
        # If cfg says preset is ON, then we shouldn't overwrite saved defaults with preset values...
        # But wait, if preset is ON starting up, what were the previous values? 
        # If preset is ON in config, the saved previous values might be lost across restarts unless saved to config.
        # However, for this session it's fine. If user starts with preset ON, restore might go to defaults or current (preset) values.
        # Let's fix loop: updateControls calls onAether, which saves current (which might be preset values if coming from config).
        # We can accept that cross-session restore might not work perfectly without config schema change, but user asked for "toggle off returns previous".
        # Assuming user enables it during session.
        self.onAetherSX2Toggled(self.cfg.preset_aethersx2)



    def onProcessProgress(self, row, pct, status_key):
        item_status = QTableWidgetItem(T(status_key, self.cfg.language))
        item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Color Logic
        if status_key == "StatusSkipped":
            item_status.setForeground(Qt.GlobalColor.gray)
        elif status_key == "StatusError":
            item_status.setForeground(Qt.GlobalColor.red)
        elif status_key == "StatusDone":
            item_status.setForeground(Qt.GlobalColor.darkGreen)
        elif status_key == "StatusCancelled":
            item_status.setForeground(Qt.GlobalColor.darkYellow)
            
        self.table.setItem(row, 2, item_status)
        
        # Global Progress
        if self.total_files_count > 0:
            total_pct = int(((self.processed_files_count * 100) + pct) / self.total_files_count)
            self.progressBar.setValue(total_pct)

    def onProcessFinished(self):
        self.btnStart.setEnabled(True)
        self.btnStop.setEnabled(False)
        self.progressBar.setVisible(False)
        self.statusLabel.setText(T("StatusDone", self.cfg.language))
        if self.chkNotifySound.isChecked(): QApplication.beep() 
        if self.chkNotifyText.isChecked():
            QMessageBox.information(self, T("MsgDoneTitle", self.cfg.language), T("MsgDoneBody", self.cfg.language))

    def downloadDATs(self):
        # Cleanup old DATs - use get_app_dir() for consistent path
        dats_folder = os.path.join(get_app_dir(), "DATs")
        if os.path.exists(dats_folder):
            try:
                import shutil
                shutil.rmtree(dats_folder)
            except: pass
            
        txt_status = "Скачивание DAT..." if self.cfg.language == "RU" else "Downloading DATs..."
        self.statusLabel.setText(txt_status)
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 100)
        self.progressBar.setFormat("%p%") 
        
        self.is_downloading = True
        self.download_thread = DownloadThread()
        self.download_thread.progress.connect(self.onDownloadProgress)
        self.download_thread.finished.connect(self.onDownloadFinished)
        self.download_thread.start()
    
    def onDownloadProgress(self, count_done, total_count, status_text):
        if total_count > 0:
            pct = int((count_done / total_count) * 100)
            self.progressBar.setValue(pct)
        self.progressBar.setFormat(status_text)
        self.statusLabel.setText(status_text)

    def onDownloadFinished(self, message_key):
        self.is_downloading = False
        self.progressBar.setVisible(False)
        self.statusLabel.setText(T(message_key, self.cfg.language))
        self.updateDATCount()
        QMessageBox.information(self, "Info", T(message_key, self.cfg.language))

    def deleteDATs(self):
        # Custom message box with translated buttons
        msg = QMessageBox(self)
        msg.setWindowTitle(T("MsgConfirmTitle", self.cfg.language) if "MsgConfirmTitle" in dir() else "Подтверждение")
        msg.setText(T("MsgConfirmDelDAT", self.cfg.language))
        msg.setIcon(QMessageBox.Icon.Question)
        
        # Add translated buttons
        yes_text = "Да" if self.cfg.language == "RU" else "Yes"
        no_text = "Нет" if self.cfg.language == "RU" else "No"
        yes_btn = msg.addButton(yes_text, QMessageBox.ButtonRole.YesRole)
        no_btn = msg.addButton(no_text, QMessageBox.ButtonRole.NoRole)
        msg.setDefaultButton(no_btn)
        
        msg.exec()
        
        if msg.clickedButton() == yes_btn:
            dats_folder = os.path.join(get_app_dir(), "DATs")
            import shutil
            try:
                if os.path.exists(dats_folder):
                    shutil.rmtree(dats_folder)
                self.statusLabel.setText(T("MsgDATsDeleted", self.cfg.language))
                QMessageBox.information(self, "Info", T("MsgDATsDeleted", self.cfg.language))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete DATs folder:\n{e}")
            
            self.updateDATCount()

    def clearCache(self):
        if clear_serial_cache():
            QMessageBox.information(self, "Success", T("MsgCacheCleared", self.cfg.language))
            
    def center(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        files = [u.toLocalFile() for u in urls]
        self.processInput(files)
        
    def processInput(self, paths):
        if self.is_downloading:
            QMessageBox.warning(self, "Info", T("MsgWaitForDownload", self.cfg.language))
            return
        self.startScan(paths)


    def onScanFinished(self):
        self.statusLabel.setText(T("LogReady", self.cfg.language))
        self.startAnalysis()

    def startAnalysis(self):
        if self.analysis_thread and self.analysis_thread.isRunning():
            return
        if not self.analysis_queue: 
            self.resetUIState()
            return

        items_to_process = list(self.analysis_queue)
        self.analysis_queue.clear()
        
        self.statusLabel.setText(T("StatusAnalyzing", self.cfg.language))
        self.analysis_thread = AnalysisThread(items_to_process, self.cfg.language)
        self.analysis_thread.progress.connect(self.updateRowStatus)
        self.analysis_thread.log.connect(self.updateLog)
        self.analysis_thread.finished.connect(self.onAnalysisFinished)
        self.analysis_thread.start()

    def onAnalysisFinished(self):
        try:
            # Auto-start conversion if requested
            if getattr(self, 'auto_start_conversion', False):
                self.auto_start_conversion = False
                self.startConversion()
                return
                
            self.statusLabel.setText(T("LogReady", self.cfg.language))
            self.resetUIState()
        except Exception as e:
            self.updateLog(f"Critical Error in onAnalysisFinished: {e}")
            try:
                self.resetUIState()
            except: pass

    def updateRowStatus(self, row, pct, status_key, sha1, serial, platform, path):
        try:
            # Prevent crash if row is invalid
            target_row = row
            
            # Verify row integrity
            if target_row >= self.table.rowCount():
                 target_row = -1
            else:
                 item = self.table.item(target_row, 0)
                 if not item or item.data(Qt.ItemDataRole.UserRole) != path:
                     target_row = -1
            
            # Fallback: Search for path (linear search)
            if target_row == -1:
                 for r in range(self.table.rowCount()):
                     item = self.table.item(r, 0)
                     if item and item.data(Qt.ItemDataRole.UserRole) == path:
                         target_row = r
                         break
            
            if target_row == -1: return # Row likely deleted
            
            # Center Status
            item_status = QTableWidgetItem(T(status_key, self.cfg.language))
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(target_row, 2, item_status) 
            
            if sha1: self.table.setItem(target_row, 8, QTableWidgetItem(sha1))      
            
            if serial: 
                # Basic validation to prevent format strings or generic tags from entering Serial column
                if serial.upper() not in ["CD-ROM", "DVD-ROM", "UNKNOWN"]:
                    item_serial = QTableWidgetItem(serial)
                    item_serial.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(target_row, 9, item_serial)  
                
            if platform: 
                self.table.setItem(target_row, 3, QTableWidgetItem(platform)) 
                # Sync to processing_items if already in there
                if hasattr(self, 'processing_items'):
                    for pi in self.processing_items:
                        if pi.get('path') == path:
                            break
        except Exception:
            pass
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete and self.table.hasFocus():
            self.deleteRow()
        else:
            super().keyPressEvent(event)
        
    def deleteRow(self):
        rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        for row in rows:
            try:
                path = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                if path in self.existing_paths:
                    self.existing_paths.remove(path)
            except: pass
            
            self.table.removeRow(row)
        
        self.lblFileCount.setText(f"{self.table.rowCount()} " + ("файлов" if self.cfg.language == "RU" else "files"))

    def loadPresetsTable(self):
        self.loading_presets = True
        self.tblPresets.setRowCount(0)
        presets = load_presets()
        for p in presets:
            self.addPresetRow(p)
        self.loading_presets = False

    def addPresetRow(self, data=None):
        self.loading_presets = True
        row = self.tblPresets.rowCount()
        self.tblPresets.insertRow(row)
        
        # Defaults
        enabled = data.get("enabled", True) if data else True
        system = data.get("system", "") if data else ""
        comp = data.get("compression", "lzma") if data else "lzma"
        cd = data.get("hunk_cd", "2352") if data else "2352"
        dvd = data.get("hunk_dvd", "4096") if data else "4096"
        
        # 0: Enabled (Widget Checkbox)
        chk_widget = QWidget()
        chk_layout = QHBoxLayout(chk_widget)
        chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chk_layout.setContentsMargins(0,0,0,0)
        chk = QCheckBox()
        chk.setChecked(enabled)
        chk.toggled.connect(lambda: self.onPresetItemChanged(None))
        chk_layout.addWidget(chk)
        self.tblPresets.setCellWidget(row, 0, chk_widget)
        
        # 1: System (Combo)
        cmb_sys = QComboBox()
        cmb_sys.setEditable(True)
        cmb_sys.lineEdit().setAlignment(Qt.AlignmentFlag.AlignLeft)
        dats_folder = os.path.join(get_app_dir(), "DATs")
        plats = get_all_platforms(dats_folder)
        cmb_sys.addItems(plats)
        cmb_sys.setCurrentText(system)
        cmb_sys.currentIndexChanged.connect(lambda: self.onPresetItemChanged(None))
        cmb_sys.lineEdit().editingFinished.connect(lambda: self.onPresetItemChanged(None))
        self.tblPresets.setCellWidget(row, 1, cmb_sys)
        
        # 2: Algo (Combobox)
        cmb_algo = QComboBox()
        cmb_algo.setEditable(True)
        cmb_algo.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        cmb_algo.lineEdit().setReadOnly(True)
        cmb_algo.addItems(["lzma", "zlib"]) 
        cmb_algo.setCurrentText(comp)
        cmb_algo.currentIndexChanged.connect(lambda: self.onPresetItemChanged(None))
        self.tblPresets.setCellWidget(row, 2, cmb_algo)
        
        # 3: CD
        cmb_cd = QComboBox()
        cmb_cd.setEditable(True)
        cmb_cd.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.populateHunkSizes(cmb_cd, "CD")
        cmb_cd.setCurrentText(str(cd))
        cmb_cd.currentIndexChanged.connect(lambda: self.onPresetItemChanged(None))
        self.tblPresets.setCellWidget(row, 3, cmb_cd)
        
        # 4: DVD
        cmb_dvd = QComboBox()
        cmb_dvd.setEditable(True)
        cmb_dvd.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.populateHunkSizes(cmb_dvd, "DVD")
        cmb_dvd.setCurrentText(str(dvd))
        cmb_dvd.currentIndexChanged.connect(lambda: self.onPresetItemChanged(None))
        self.tblPresets.setCellWidget(row, 4, cmb_dvd)
        
        # 5: Comment
        comment = data.get("comment", "") if data else ""
        self.tblPresets.setItem(row, 5, QTableWidgetItem(comment))
        
        self.loading_presets = False

    def deletePresetRow(self):
        row = self.tblPresets.currentRow()
        if row >= 0:
            self.tblPresets.removeRow(row)
            self.onPresetItemChanged(None)

    def onPresetItemChanged(self, item):
        if not getattr(self, "loading_presets", False):
            self.savePresetsFromTable()

    def savePresetsFromTable(self):
        presets = []
        for row in range(self.tblPresets.rowCount()):
            widget_chk = self.tblPresets.cellWidget(row, 0)
            if not widget_chk: continue
            chk = widget_chk.findChild(QCheckBox)
            enabled = chk.isChecked() if chk else True
            
            w_sys = self.tblPresets.cellWidget(row, 1)
            system = w_sys.currentText() if w_sys else ""
            
            cmb_algo = self.tblPresets.cellWidget(row, 2)
            comp = cmb_algo.currentText() if cmb_algo else "lzma"
            
            cmb_cd = self.tblPresets.cellWidget(row, 3)
            cd = cmb_cd.currentText() if cmb_cd else "2352"
            
            cmb_dvd = self.tblPresets.cellWidget(row, 4)
            dvd = cmb_dvd.currentText() if cmb_dvd else "4096"
            
            item_comment = self.tblPresets.item(row, 5)
            comment = item_comment.text() if item_comment else ""
            
            if system:
                presets.append({
                    "enabled": enabled,
                    "system": system,
                    "compression": comp,
                    "hunk_cd": cd,
                    "hunk_dvd": dvd,
                    "comment": comment
                })

    
    # --- File Management & UI Events ---
    
    def addFiles(self):
        files, _ = QFileDialog.getOpenFileNames(self, T("btnAddFiles", self.cfg.language), "", "Disc Images (*.cue *.gdi *.iso *.chd *.mds *.nrg *.ccd *.img *.toc)")
        if files:
            self.startScan([f for f in files])

    def addFolder(self):
        folder = QFileDialog.getExistingDirectory(self, T("btnAddFolder", self.cfg.language))
        if folder:
            self.startScan([folder])
            
    def clearList(self):
        self.table.setRowCount(0)
        self.lblFileCount.setText("0 files")
        self.items_data = [] # Reset internal data list if used, or just rely on table? 
        # Better to have an internal list or re-scan from table. 
        # For simplicity, we'll assume we scan into table.
        # Check startProcessing logic later.
        
    def browseOutput(self):
        folder = QFileDialog.getExistingDirectory(self, T("lblOutput", self.cfg.language))
        if folder:
            self.txtOutput.setText(folder)
            
    def onOutputChanged(self, text):
        self.cfg.output_folder = text
        
    def startScan(self, paths):
        # Disable buttons
        self.btnAddFiles.setEnabled(False)
        self.btnAddFolder.setEnabled(False)
        self.statusLabel.setText(T("StatusScanningFiles", self.cfg.language))
        
        self.scan_thread = ScanThread(paths)
        self.scan_thread.filesFound.connect(self.onScanFilesFound)
        self.scan_thread.finished.connect(self.onScanFinished)
        self.scan_thread.start()
        
    def onScanFilesFound(self, batch):
        # Files/folders to skip (not game images)
        SKIP_PATTERNS = ['storm', 'chdman', 'python', 'setup', 'readme', 'license', 'changelog']
        SKIP_EXTENSIONS = ['.exe', '.dll', '.py', '.txt', '.md', '.bat', '.sh']
        
        # batch is list of dicts
        for data in batch:
            path = data['path']
            
            # Skip non-game files
            basename = os.path.basename(path).lower()
            ext = os.path.splitext(path)[1].lower()
            
            # Check if file should be skipped
            if any(skip in basename for skip in SKIP_PATTERNS):
                continue
            if ext in SKIP_EXTENSIONS:
                continue
            
            # Optimized Duplicate Check
            if path in self.existing_paths:
                continue
            
            self.existing_paths.add(path)
            
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # 0: File
            item_file = QTableWidgetItem(data['display_name'])
            item_file.setToolTip(path)
            item_file.setData(Qt.ItemDataRole.UserRole, path)
            item_file.setFlags(item_file.flags() | Qt.ItemFlag.ItemIsEditable) 
            self.table.setItem(row, 0, item_file)
            
            # 1: Count (show '-' for pending values)
            count_text = "-" if data['count'] == -1 else str(data['count'])
            item_count = QTableWidgetItem(count_text)
            item_count.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, item_count)
            
            # 2: Status
            item_status = QTableWidgetItem(T("StatusAdded", self.cfg.language))
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, item_status)
            
            self.updateLog(f"{T('LogAdded', self.cfg.language)} {data['display_name']}")
            
            # 3: Platform
            self.table.setItem(row, 3, QTableWidgetItem(""))
            
            # 4: Format
            item_fmt = QTableWidgetItem(data['format'])
            item_fmt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, item_fmt)
            
            # 5: Size
            item_size = QTableWidgetItem(data['readable_size'])
            item_size.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_size.setData(Qt.ItemDataRole.UserRole, data['size'])
            self.table.setItem(row, 5, item_size)
            
            # 6: End Size
            self.table.setItem(row, 6, QTableWidgetItem(""))
            
            # 7: Diff
            self.table.setItem(row, 7, QTableWidgetItem(""))
            
            # 8: SHA1
            self.table.setItem(row, 8, QTableWidgetItem(""))
            
            # 9: Serial
            self.table.setItem(row, 9, QTableWidgetItem(""))
            
            self.analysis_queue.append({'row': row, 'path': path})
            
            # Auto-start analysis if idle
            if self.scan_thread and self.scan_thread.isRunning():
                 # While scanning, maybe wait till batch end? 
                 # Or start immediately if thread not running
                 pass
            
            if not self.analysis_thread or not self.analysis_thread.isRunning():
                 # We can start analysis on this batch immediately?
                 # Need to be careful about threading.
                 # Let's rely on onScanFinished or explicit trigger for now, 
                 # OR simple check:
                 pass
            # Trigger analysis immediately for better responsiveness?
            # If we do this, we need to make sure startAnalysis handles concurrency or we serialize it.
            # My logic in startAnalysis consumes the queue. 
            # So if we call it, it picks up what's there.
            if not (self.analysis_thread and self.analysis_thread.isRunning()):
                 # Use QTimer to debounce or just call it?
                 # Calling directly might be safe if on main thread.
                 # self.startAnalysis() 
                 pass # Let's stick to onScanFinished for stability first, or maybe debounce.
                 

            # Queue for Info Thread if needed
            if data['size'] == -1:
                self.info_queue.append((row, path))
            
            self.lblFileCount.setText(f"{self.table.rowCount()} " + ("файлов" if self.cfg.language == "RU" else "files"))
        
        # Start Info Thread if items queued
        if self.info_queue:
            batch_queue = list(self.info_queue)
            self.info_queue.clear()
            
            self.temp_info_thread = InfoThread(batch_queue)
            self.temp_info_thread.infoReady.connect(self.onInfoReady)
            self.temp_info_thread.start()
            
            if not hasattr(self, 'info_threads'): self.info_threads = []
            self.info_threads.append(self.temp_info_thread)
            # Use default argument ensuring local variable is captured properly or passed
            self.temp_info_thread.finished.connect(lambda t=self.temp_info_thread: self.cleanupInfoThread(t))

    def cleanupInfoThread(self, thread):
        if hasattr(self, 'info_threads') and thread in self.info_threads:
            self.info_threads.remove(thread)

    def onInfoReady(self, row, size, readable_size, count, fmt):
        if row < self.table.rowCount():
            # Update Size (Col 5)
            item_size = QTableWidgetItem(readable_size)
            item_size.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_size.setData(Qt.ItemDataRole.UserRole, size)
            self.table.setItem(row, 5, item_size)
            
            # Update Count (Col 1)
            item_count = QTableWidgetItem(str(count))
            item_count.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, item_count)
            
            # Update Format (Col 4)
            item_fmt = QTableWidgetItem(fmt)
            item_fmt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, item_fmt)

    def onScanFinished(self):
        self.loading_presets = False
        self.progressBar.setVisible(False)
        self.lblFileCount.setText(f"{self.table.rowCount()} " + ("файлов" if self.cfg.language == "RU" else "files"))
        
        # Trigger Analysis if not already running
        if self.analysis_queue and not (self.analysis_thread and self.analysis_thread.isRunning()):
            self.startAnalysis()
        elif not (self.analysis_thread and self.analysis_thread.isRunning()):
            # No analysis needed -> Re-enable buttons
            self.btnAddFiles.setEnabled(True)
            self.btnAddFolder.setEnabled(True)
            if hasattr(self, 'boxPresets'): self.boxPresets.setEnabled(True)
            if hasattr(self, 'boxOutputFolders'): self.boxOutputFolders.setEnabled(True)

    def startAnalysis(self):
        if not self.analysis_queue:
            return

        self.btnStart.setEnabled(False)
        self.btnStop.setEnabled(True)
        self.btnAddFiles.setEnabled(False)
        self.btnAddFolder.setEnabled(False)
        # self.progressBar.setVisible(True) # Optional for global progress

        # Take all current items
        items_to_process = list(self.analysis_queue)
        self.analysis_queue.clear() # Clear queue

        self.analysis_thread = AnalysisThread(items_to_process, self.cfg.language)
        self.analysis_thread.progress.connect(self.onAnalysisProgress)
        self.analysis_thread.log.connect(self.updateLog)
        self.analysis_thread.finished.connect(self.onAnalysisFinished)
        self.analysis_thread.start()

    def onAnalysisProgress(self, row, pct, status_key, sha1, serial, platform, path):
        if row < self.table.rowCount():
            # Update Status
            item_status = QTableWidgetItem(T(status_key, self.cfg.language))
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, item_status)

            if sha1:
                self.table.setItem(row, 8, QTableWidgetItem(sha1))
            
            if serial:
                self.table.setItem(row, 9, QTableWidgetItem(serial))
                
            if platform:
                self.table.setItem(row, 3, QTableWidgetItem(platform))
                
                # Auto-select preset if available
                # (Logic from previous implementation if needed, omitted for brevity)

    def onAnalysisFinished(self):
        # Check if more items arrived while analyzing
        if self.analysis_queue:
            self.startAnalysis()
        else:
            self.btnStart.setEnabled(True)
            self.btnStop.setEnabled(False)
            self.progressBar.setVisible(False)
            self.statusLabel.setText(T("StatusReady", self.cfg.language))
            
            # Re-enable inputs
            self.btnAddFiles.setEnabled(True)
            self.btnAddFolder.setEnabled(True)
            if hasattr(self, 'boxPresets'): self.boxPresets.setEnabled(True)
            if hasattr(self, 'boxOutputFolders'): self.boxOutputFolders.setEnabled(True)


    def showContextMenu(self, pos):
        menu = QMenu(self)
        
        actDelete = QAction(T("menuContextDelete", self.cfg.language), self)
        actDelete.triggered.connect(lambda: self.table.removeRow(self.table.currentRow()))
        menu.addAction(actDelete)
        
        # Process Selected
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()))
        count = len(selected_rows)
        if count > 0:
            txt = T("menuContextProcess", self.cfg.language)
            if count > 1:
                txt += f" ({count})"
            actProcess = QAction(txt, self)
            actProcess.triggered.connect(lambda: self.processSelectedRows(selected_rows))
            menu.addAction(actProcess)
            
            # Rehash Selected
            txt_rehash = T("menuContextRehash", self.cfg.language)
            if count > 1:
                txt_rehash += f" ({count})"
            actRehash = QAction(txt_rehash, self)
            actRehash.triggered.connect(lambda: self.rehashSelectedRows(selected_rows))
            menu.addAction(actRehash)
        
        actOpenSrc = QAction(T("menuContextOpenSrc", self.cfg.language), self)
        actOpenSrc.triggered.connect(self.openSourceFolder)
        menu.addAction(actOpenSrc)
        
        menu.exec(self.table.mapToGlobal(pos))
        
    def openSourceFolder(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                path = item.toolTip()
                folder = os.path.dirname(path)
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def onCellChanged(self, row, col):
        if col == 0:
            # Maybe update some internal struct if we had one?
            pass

    def closeEvent(self, event):
        # Save geometry
        size = self.size()
        self.cfg.window_size = [size.width(), size.height()]
        
        # Save Columns
        widths = []
        for i in range(self.table.columnCount()):
            widths.append(self.table.columnWidth(i))
        self.cfg.column_widths = widths
        
        self.cfg.save()
        event.accept()

    # --- Processing Logic ---

    # --- Processing Logic ---
    
    def processSelectedRows(self, rows):
        self.startProcessing(rows)
    
    def rehashSelectedRows(self, rows):
        """Clear cache and re-analyze selected rows."""
        from src.logic import remove_from_serial_cache
        
        items_to_analyze = []
        for row in rows:
            item_file = self.table.item(row, 0)
            if item_file:
                path = item_file.toolTip()
                filename = item_file.text()
                
                # Remove from cache
                remove_from_serial_cache(filename)
                
                # Clear displayed values
                self.table.setItem(row, 2, QTableWidgetItem(T("StatusAdded", self.cfg.language)))
                self.table.setItem(row, 8, QTableWidgetItem(""))  # SHA1
                self.table.setItem(row, 9, QTableWidgetItem(""))  # Serial
                
                items_to_analyze.append({'row': row, 'path': path})
        
        # Re-analyze
        if items_to_analyze:
            self.analysis_queue = items_to_analyze
            self.startAnalysis()

    def startProcessing(self, rows=None):
        if self.table.rowCount() == 0:
            return
            
        # Collect items
        self.processing_items = []
        
        target_rows = rows if rows is not None else range(self.table.rowCount())
        
        for row in target_rows:
            item_file = self.table.item(row, 0)
            item_format = self.table.item(row, 4)
            item_platform = self.table.item(row, 3)
            path = item_file.toolTip()
            display_name = item_file.text()
            fmt = item_format.text()
            plat_txt = item_platform.text() if item_platform else ""
            
            self.processing_items.append({
                "row": row,
                "path": path,
                "display_name": display_name,
                "format": fmt,
                "platform": plat_txt
            })
            
            # Reset Status
            item_added = QTableWidgetItem(T("StatusAdded", self.cfg.language))
            item_added.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, item_added)
            
        # Sync Settings from UI to Config
        self.cfg.force_overwrite = self.chkOverwrite.isChecked()
        self.cfg.platform_recognition = self.chkRecognition.isChecked()
        self.cfg.extract_subfolders = self.chkExtractSubfolders.isChecked()
        self.cfg.delete_source = self.chkDeleteSource.isChecked()
        self.cfg.preset_aethersx2 = self.chkAetherSX2.isChecked()
        self.cfg.auto_update = self.chkAutoUpdate.isChecked()
        self.cfg.notify_text = self.chkNotifyText.isChecked()
        self.cfg.notify_sound = self.chkNotifySound.isChecked()
        self.cfg.log_font_enabled = self.chkLogFont.isChecked()
        self.cfg.log_font_size = self.spnLogFont.value()
        self.cfg.compression = self.cmbCompression.currentText()
        try:
            txt = self.cmbThreads.currentText()
            if "Auto" in txt: self.cfg.threads = 0
            else: self.cfg.threads = int(txt)
        except: self.cfg.threads = 0
        self.cfg.hunk_cd = self.cmbHunkCD.currentText()
        self.cfg.hunk_dvd = self.cmbHunkDVD.currentText()
        self.cfg.save()
            
        self.btnStart.setEnabled(False)
        self.btnStop.setEnabled(True)
        # Disable Settings Tab entirely to prevent changes during processing
        if hasattr(self, 'tabSettings'):
             self.tabSettings.setEnabled(False)
        
        # Disable main inputs
        self.btnAddFiles.setEnabled(False)
        self.btnAddFolder.setEnabled(False)
        self.btnClear.setEnabled(False)
        if hasattr(self, 'boxPresets'): self.boxPresets.setEnabled(False)
        if hasattr(self, 'boxOutputFolders'): self.boxOutputFolders.setEnabled(False)
        
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        
        # Check if analysis is needed (queue not empty) or force check?
        # Actually startAnalysis checks queue. If queue empty, it returns immediately (and calls resetUIState!).
        # So we should prevent resetUIState if we want to run conversion.
        
        if self.analysis_queue:
            self.auto_start_conversion = True
            self.startAnalysis()
        else:
            self.startConversion()

    def stopProcessing(self):
        if hasattr(self, 'analysis_thread') and self.analysis_thread.isRunning():
            self.analysis_thread.stop()
        if hasattr(self, 'conversion_thread') and self.conversion_thread.isRunning():
            self.conversion_thread.stop()
        self.resetUIState()
        self.statusLabel.setText(T("StatusCancelled", self.cfg.language))

    def resetUIState(self):
        self.btnStart.setEnabled(True)
        self.btnStop.setEnabled(False)
        
        # Re-enable Settings Tab
        if hasattr(self, 'tabSettings'):
             self.tabSettings.setEnabled(True)
             
        # Re-enable main inputs
        self.btnAddFiles.setEnabled(True)
        self.btnAddFolder.setEnabled(True)
        self.btnClear.setEnabled(True)
        if hasattr(self, 'boxPresets'): self.boxPresets.setEnabled(True)
        if hasattr(self, 'boxOutputFolders'): self.boxOutputFolders.setEnabled(True)
        
        self.progressBar.setVisible(False)
        QApplication.restoreOverrideCursor() # Final restore just in case

    # -- v1.1.0 Features --
    
    def onMinimizeTrayToggled(self, checked):
        self.cfg.minimize_to_tray = checked
        self.cfg.save()
        
    def onCloseTrayToggled(self, checked):
        self.cfg.close_to_tray = checked
        self.cfg.save()
        
    def onExtractSubfoldersToggled(self, checked):
        self.cfg.extract_subfolders = checked
        self.cfg.save()

    def onDeleteSourceToggled(self, checked):
        self.cfg.delete_source = checked
        self.cfg.save()

    def onLogFontEnabledToggled(self, checked):
        self.cfg.log_font_enabled = checked
        self.cfg.save()
        self.spnLogFont.setEnabled(checked)
        self.updateLogStyle()
        
    def onLogFontChanged(self, value):
        self.cfg.log_font_size = value
        self.cfg.save()
        self.updateLogStyle()
        
    def initTray(self):
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(self.windowIcon())
        
        # Tray Menu
        trayMenu = QMenu()
        restoreAction = QAction("Restore", self)
        restoreAction.triggered.connect(self.showNormal)
        quitAction = QAction("Exit", self)
        quitAction.triggered.connect(QApplication.instance().quit)
        
        trayMenu.addAction(restoreAction)
        trayMenu.addAction(quitAction)
        
        self.trayIcon.setContextMenu(trayMenu)
        self.trayIcon.activated.connect(self.trayIconActivated)
        self.trayIcon.show()
        
    def trayIconActivated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()
                
    def changeEvent(self, event):
        if event.type() == 105: # QEvent.WindowStateChange
            if self.isMinimized() and self.cfg.minimize_to_tray:
                self.hide()
        super().changeEvent(event)

    # -- Conversion Phase --

    def startConversion(self):
        self.statusLabel.setText(T("StatusProcessing", self.cfg.language))
        
        # Prepare Options
        options = {
            "output_folder": self.cfg.output_folder,
            "threads": self.cfg.threads, 
            "compression": self.cfg.compression,
            "hunk_cd": self.cfg.hunk_cd,
            "hunk_dvd": self.cfg.hunk_dvd,
            "force": self.cfg.force_overwrite,
            "platform_recognition": self.cfg.platform_recognition,
            "recognition": self.cfg.platform_recognition,
            "language": self.cfg.language,
            "presets": load_presets(),
            "extract_subfolders": self.cfg.extract_subfolders,
            "platform_output_folders": self.cfg.platform_output_folders
        }
        
        self.conversion_thread = ConversionThread(self.processing_items, options)
        self.conversion_thread.progress.connect(self.onConversionProgress)
        self.conversion_thread.fileFinished.connect(self.onFileFinished)
        self.conversion_thread.logOutput.connect(self.updateLog)
        self.conversion_thread.finished.connect(self.onConversionFinished)
        self.conversion_thread.start()

    def onConversionProgress(self, row, pct, status_key):
        item = QTableWidgetItem(T(status_key, self.cfg.language))
        if pct >= 0 and status_key == "StatusProcessing":
            item.setText(f"{T(status_key, self.cfg.language)} {pct}%")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 2, item)
    
    def _parse_size_text(self, text):
        """Parse size text like '3.72 GB' back to bytes."""
        try:
            import re
            match = re.match(r'([\d.]+)\s*([KMGT]?B)', text.strip().upper())
            if match:
                value = float(match.group(1))
                unit = match.group(2)
                multipliers = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
                return int(value * multipliers.get(unit, 1))
        except:
            pass
        return 0
                
    def onFileFinished(self, row, size_bytes):
        readable = get_readable_size(size_bytes)
        item_end = QTableWidgetItem(readable)
        item_end.setData(Qt.ItemDataRole.UserRole, size_bytes)
        item_end.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 6, item_end)
        
        # Calculate Diff
        item_start = self.table.item(row, 5)
        if item_start:
            start_bytes = item_start.data(Qt.ItemDataRole.UserRole)
            
            # Ensure start_bytes is a number, with fallback to parse from text
            try:
                if start_bytes is not None:
                    start_bytes = int(start_bytes)
                    # If data is -1 (pending), try to parse from text
                    if start_bytes <= 0:
                        start_bytes = self._parse_size_text(item_start.text())
                else:
                    start_bytes = self._parse_size_text(item_start.text())
            except (ValueError, TypeError):
                start_bytes = self._parse_size_text(item_start.text())
            
            if start_bytes and start_bytes > 0:
                diff_bytes = start_bytes - size_bytes
                diff_readable = get_readable_size(abs(diff_bytes))
                
                # Ratio: (end/start * 100)%
                ratio = (size_bytes / start_bytes) * 100
                
                # Determine sign and color
                prefix = ""
                from PyQt6.QtGui import QColor
                color = None
                
                if size_bytes < start_bytes:
                    prefix = "-"
                    color = QColor("#00FF00") # Green for save
                elif size_bytes > start_bytes:
                    prefix = "+"
                    color = QColor("#FF4444") # Red for grow
                
                diff_pct = ratio - 100.0
                diff_text = f"{prefix}{diff_readable} ({diff_pct:+.2f}%)"
                
                item_diff = QTableWidgetItem(diff_text)
                item_diff.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if color:
                    item_diff.setForeground(color)
                    
                self.table.setItem(row, 7, item_diff)
                
        if len(self.processing_items) > 0:
            self.progressBar.setValue(int(((row + 1) / len(self.processing_items)) * 100))
        
        # Update general info after each file
        self.updateGeneralInfo()

    def onConversionFinished(self):
        self.resetUIState()
        self.statusLabel.setText(T("MsgDoneTitle", self.cfg.language))
        QMessageBox.information(self, T("MsgDoneTitle", self.cfg.language), T("MsgDoneBody", self.cfg.language))

    def updateLog(self, text):
        self.txtLog.append(text)
        sb = self.txtLog.verticalScrollBar()
        sb.setValue(sb.maximum())


