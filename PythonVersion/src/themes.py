# src/themes.py

# Helper to compute a slightly darker color for gradient effect
def _darker_color(hex_color, factor=15):
    """Make a hex color darker by factor percent. Works with solid colors only."""
    if hex_color.startswith('qlineargradient') or hex_color.startswith('qradialgradient'):
        return hex_color  # Return as-is for gradients
    try:
        hex_color = hex_color.lstrip('#')
        r = max(0, int(hex_color[0:2], 16) - factor * 255 // 100)
        g = max(0, int(hex_color[2:4], 16) - factor * 255 // 100)
        b = max(0, int(hex_color[4:6], 16) - factor * 255 // 100)
        return f"#{r:02x}{g:02x}{b:02x}"
    except:
        return hex_color

# Function to generate QSS from a theme dictionary - Modern UI Style
def get_qss(t, font_size_pt=8):
    # Compute darker button color for gradient effect
    btn_color = t['ButtonColor']
    if btn_color.startswith('qlineargradient'):
        btn_gradient = btn_color
        btn_hover_gradient = t['ButtonHover']
    else:
        darker_btn = _darker_color(btn_color, 15)
        btn_gradient = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {btn_color}, stop:1 {darker_btn})"
        hover_color = t['ButtonHover']
        if not hover_color.startswith('qlineargradient'):
            darker_hover = _darker_color(hover_color, 10)
            btn_hover_gradient = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {hover_color}, stop:1 {darker_hover})"
        else:
            btn_hover_gradient = hover_color
    
    return f"""
    /* === MAIN WINDOW === */
    QMainWindow, QDialog {{
        background-color: {t['BackColor']};
        color: {t['ForeColor']};
        font-family: "Century Gothic", "Segoe UI", sans-serif;
        font-size: {font_size_pt}pt;
    }}
    
    /* === BASE WIDGET === */
    QWidget {{
        background-color: {t['BackColor']};
        color: {t['ForeColor']};
        font-family: "Century Gothic", "Segoe UI", sans-serif;
        font-size: {font_size_pt}pt;
    }}
    
    /* === LABELS === */
    QLabel {{
        color: {t['ForeColor']};
        background-color: transparent;
        font-family: "Century Gothic", "Segoe UI", sans-serif;
    }}
    
    /* === TABS === */
    QTabWidget::pane {{
        border: 1px solid {t['BorderColor']};
        background: {t['BackColor']};
        border-radius: 4px;
    }}
    QTabBar::tab {{
        background: {btn_gradient};
        color: {t['FieldForeColor']};
        padding: 8px 20px;
        border: 1px solid {t['BorderColor']};
        border-bottom: 2px solid {t['BorderColor']};
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        margin-right: 2px;
        font-family: "Century Gothic", "Segoe UI", sans-serif;
        font-weight: bold;
    }}
    QTabBar::tab:hover {{
        background: {btn_hover_gradient};
        border-bottom: 2px solid {t['CheckColor']};
    }}
    QTabBar::tab:selected {{
        background: {t['BackColor']};
        color: {t['ForeColor']};
        border-top: 2px solid {t['CheckColor']};
        border-bottom: 2px solid {t['BackColor']};
    }}
    
    /* === GROUP BOX === */
    QGroupBox {{
        border: 1px solid {t['BorderColor']};
        border-radius: 6px;
        margin-top: 14px;
        padding-top: 12px;
        font-weight: bold;
        background-color: {t['BackColor']};
        font-family: "Century Gothic", "Segoe UI", sans-serif;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: {t['CheckColor']};
        font-weight: bold;
    }}
    
    /* === BUTTONS - Modern Gradient Style === */
    QPushButton {{
        background: {btn_gradient};
        color: {t['FieldForeColor']};
        border: 1px solid {t['BorderColor']};
        border-bottom: 2px solid {t['BorderColor']};
        padding: 6px 14px;
        border-radius: 4px;
        font-family: "Century Gothic", "Segoe UI", sans-serif;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background: {btn_hover_gradient};
        border-bottom: 2px solid {t['CheckColor']};
    }}
    QPushButton:pressed {{
        border-bottom: 1px solid {t['BorderColor']};
        margin-top: 1px;
    }}
    QPushButton:disabled {{
        background: {t['FieldBackColor']};
        color: {t['BorderColor']};
        border: 1px solid {t['BorderColor']};
    }}
    
    /* === INPUT FIELDS === */
    QLineEdit, QSpinBox {{
        background-color: {t['FieldBackColor']};
        color: {t['FieldForeColor']};
        border: 1px solid {t['BorderColor']};
        border-radius: 4px;
        padding: 5px 8px;
        font-family: "Century Gothic", "Segoe UI", sans-serif;
        selection-background-color: {t['CheckColor']};
    }}
    QLineEdit:focus, QSpinBox:focus {{
        border: 1px solid {t['CheckColor']};
    }}
    
    /* === COMBOBOX === */
    QComboBox {{
        background-color: {t['FieldBackColor']};
        color: {t['FieldForeColor']};
        border: 1px solid {t['BorderColor']};
        border-radius: 4px;
        padding: 5px 8px;
        font-family: "Century Gothic", "Segoe UI", sans-serif;
    }}
    QComboBox:hover {{
        border: 1px solid {t['CheckColor']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
        subcontrol-origin: padding;
        subcontrol-position: right center;
        background: {t['ButtonColor']};
        border-left: 1px solid {t['BorderColor']};
        border-top-right-radius: 4px;
        border-bottom-right-radius: 4px;
    }}
    QComboBox::down-arrow {{
        width: 0;
        height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {t['FieldForeColor']};
    }}
    QComboBox QAbstractItemView {{
        background-color: {t['FieldBackColor']};
        color: {t['FieldForeColor']};
        selection-background-color: {t['ButtonColor']};
        selection-color: {t['ForeColor']};
        border: 1px solid {t['BorderColor']};
    }}
    
    /* === SPINBOX ARROWS === */
    QSpinBox::up-button, QSpinBox::down-button {{
        width: 18px;
        background: {t['ButtonColor']};
        border: 1px solid {t['BorderColor']};
        border-radius: 2px;
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background: {t['ButtonHover']};
    }}
    QSpinBox::up-arrow {{
        width: 0;
        height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 5px solid {t['FieldForeColor']};
    }}
    QSpinBox::down-arrow {{
        width: 0;
        height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {t['FieldForeColor']};
    }}
    
    /* === TABLE WIDGET === */
    QTableWidget {{
        background-color: {t['FieldBackColor']};
        color: {t['FieldForeColor']};
        gridline-color: {t['BorderColor']};
        border: 1px solid {t['BorderColor']};
        border-radius: 4px;
        font-family: "Century Gothic", "Segoe UI", sans-serif;
        alternate-background-color: {_darker_color(t['FieldBackColor'], 5)};
    }}
    QTableWidget::item {{
        padding: 4px;
    }}
    QTableWidget::item:selected {{
        background-color: {t['CheckColor']};
        color: {t['BackColor']};
    }}
    
    /* === HEADER VIEW === */
    QHeaderView::section {{
        background: {btn_gradient};
        color: {t['FieldForeColor']};
        border: 1px solid {t['BorderColor']};
        padding: 6px;
        font-family: "Century Gothic", "Segoe UI", sans-serif;
        font-weight: bold;
    }}
    
    /* === CHECKBOX === */
    QCheckBox {{
        spacing: 8px;
        color: {t['ForeColor']};
        font-family: "Century Gothic", "Segoe UI", sans-serif;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {t['BorderColor']};
        border-radius: 3px;
        background: {t['FieldBackColor']};
    }}
    QCheckBox::indicator:hover {{
        border: 1px solid {t['CheckColor']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {t['CheckColor']};
        border-color: {t['CheckColor']};
    }}
    
    /* === PROGRESS BAR === */
    QProgressBar {{
        border: 1px solid {t['BorderColor']};
        border-radius: 4px;
        background-color: {t['FieldBackColor']};
        text-align: center;
        color: {t['ForeColor']};
        height: 20px;
        font-family: "Century Gothic", "Segoe UI", sans-serif;
        font-weight: bold;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {t['CheckColor']}, stop:1 {_darker_color(t['CheckColor'], 20)});
        border-radius: 3px;
    }}
    
    /* === SCROLL BARS === */
    QScrollBar:vertical {{
        background: {t['FieldBackColor']};
        width: 12px;
        border: none;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical {{
        background: {t['ButtonColor']};
        min-height: 30px;
        border-radius: 5px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {t['ButtonHover']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: {t['FieldBackColor']};
        height: 12px;
        border: none;
        border-radius: 6px;
    }}
    QScrollBar::handle:horizontal {{
        background: {t['ButtonColor']};
        min-width: 30px;
        border-radius: 5px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {t['ButtonHover']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    
    /* === TEXT EDIT (Log) === */
    QTextEdit {{
        background-color: {t['FieldBackColor']};
        color: {t['FieldForeColor']};
        border: 1px solid {t['BorderColor']};
        border-radius: 4px;
        font-family: Consolas, "Courier New", monospace;
        padding: 4px;
    }}
    
    /* === MENU === */
    QMenu {{
        background-color: {t['BackColor']};
        border: 1px solid {t['BorderColor']};
        border-radius: 4px;
        padding: 4px;
        font-family: "Century Gothic", "Segoe UI", sans-serif;
    }}
    QMenu::item {{
        padding: 8px 25px;
        background-color: transparent;
        color: {t['ForeColor']};
    }}
    QMenu::item:selected {{
        background-color: {t['ButtonColor']};
        color: {t['ForeColor']};
        border-radius: 4px;
    }}
    
    /* === MENU BAR === */
    QMenuBar {{
        background-color: {t['BackColor']};
        color: {t['ForeColor']};
        border-bottom: 1px solid {t['BorderColor']};
        font-family: "Century Gothic", "Segoe UI", sans-serif;
    }}
    QMenuBar::item {{
        padding: 6px 12px;
        background-color: transparent;
    }}
    QMenuBar::item:selected {{
        background-color: {t['ButtonColor']};
        border-radius: 4px;
    }}
    
    /* === STATUS BAR === */
    QStatusBar {{
        background-color: {t['FieldBackColor']};
        color: {t['ForeColor']};
        border-top: 1px solid {t['BorderColor']};
        font-family: "Century Gothic", "Segoe UI", sans-serif;
    }}
    
    /* === TOOL BUTTON === */
    QToolButton {{
        background: {btn_gradient};
        color: {t['FieldForeColor']};
        border: 1px solid {t['BorderColor']};
        border-radius: 4px;
        padding: 4px;
        font-family: "Century Gothic", "Segoe UI", sans-serif;
    }}
    QToolButton:hover {{
        background: {btn_hover_gradient};
        border: 1px solid {t['CheckColor']};
    }}
    
    /* === SCROLL AREA === */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    
    /* === FRAME === */
    QFrame#SettingsFrame {{
        border: 1px solid {t['BorderColor']};
        border-radius: 6px;
        background-color: {_darker_color(t['BackColor'], 3)};
    }}
    """

THEMES = [
    { "Name": "Charcoal Dark", "BackColor": "#2D2D2D", "ForeColor": "#E0E0E0", "ButtonColor": "#3C3C3C", "ButtonHover": "#4A4A4A", "FieldBackColor": "#3C3C3C", "FieldForeColor": "#E0E0E0", "HeaderColor": "#1A1A1A", "BorderColor": "#808080", "CheckColor": "#00FF00" },
    { "Name": "Steel Storm", "BackColor": "#1C2526", "ForeColor": "#FFFFFF", "ButtonColor": "#2A3F4D", "ButtonHover": "#3B5B73", "FieldBackColor": "#2A3F4D", "FieldForeColor": "#FFFFFF", "HeaderColor": "#0D1517", "BorderColor": "#5A9FB5", "CheckColor": "#4ADE80" },
    { "Name": "Platinum Light", "BackColor": "#F0F0F0", "ForeColor": "#000000", "ButtonColor": "#D3D3D3", "ButtonHover": "#B0B0B0", "FieldBackColor": "#FFFFFF", "FieldForeColor": "#000000", "HeaderColor": "#E0E0E0", "BorderColor": "#808080", "CheckColor": "#22C55E" },
    { "Name": "Ocean Depth", "BackColor": "#1E3A8A", "ForeColor": "#FFFFFF", "ButtonColor": "#3B82F6", "ButtonHover": "#60A5FA", "FieldBackColor": "#3B82F6", "FieldForeColor": "#FFFFFF", "HeaderColor": "#0F1F4A", "BorderColor": "#93C5FD", "CheckColor": "#60A5FA" },
    { "Name": "Emerald Forest", "BackColor": "#14532D", "ForeColor": "#FFFFFF", "ButtonColor": "#22C55E", "ButtonHover": "#4ADE80", "FieldBackColor": "#22C55E", "FieldForeColor": "#FFFFFF", "HeaderColor": "#0A2917", "BorderColor": "#86EFAC", "CheckColor": "#4ADE80" },
    { "Name": "Amethyst", "BackColor": "#4C1D95", "ForeColor": "#FFFFFF", "ButtonColor": "#8B5CF6", "ButtonHover": "#A78BFA", "FieldBackColor": "#8B5CF6", "FieldForeColor": "#FFFFFF", "HeaderColor": "#2E0F5B", "BorderColor": "#C4B5FD", "CheckColor": "#A78BFA" },
    { "Name": "Volcano", "BackColor": "#7C2D12", "ForeColor": "#FFFFFF", "ButtonColor": "#F97316", "ButtonHover": "#FB923C", "FieldBackColor": "#F97316", "FieldForeColor": "#FFFFFF", "HeaderColor": "#3E1709", "BorderColor": "#FED7AA", "CheckColor": "#FB923C" },
    { "Name": "Blood Ruby", "BackColor": "#450A0A", "ForeColor": "#FFFFFF", "ButtonColor": "#EF4444", "ButtonHover": "#F87171", "FieldBackColor": "#EF4444", "FieldForeColor": "#FFFFFF", "HeaderColor": "#230505", "BorderColor": "#FECACA", "CheckColor": "#F87171" },
    { "Name": "Gothic", "BackColor": "#101010", "ForeColor": "#C0C0C0", "ButtonColor": "#2E0000", "ButtonHover": "#5A0000", "FieldBackColor": "#1A1A1A", "FieldForeColor": "#E0E0E0", "HeaderColor": "#000000", "BorderColor": "#505050", "CheckColor": "#8B0000" },
    { "Name": "Metallic", "BackColor": "#43464B", "ForeColor": "#FFFFFF", "ButtonColor": "#71797E", "ButtonHover": "#BCC6CC", "FieldBackColor": "#55555C", "FieldForeColor": "#E0E0E0", "HeaderColor": "#2C2F33", "BorderColor": "#BCC6CC", "CheckColor": "#71797E" },
    { "Name": "Steam Engine", "BackColor": "#4A2C2A", "ForeColor": "#F3E5AB", "ButtonColor": "#B87333", "ButtonHover": "#CD7F32", "FieldBackColor": "#804A00", "FieldForeColor": "#F3E5AB", "HeaderColor": "#2F1E19", "BorderColor": "#D4AF37", "CheckColor": "#B87333" },
    { "Name": "Deep Woods", "BackColor": "#0A210F", "ForeColor": "#C2B280", "ButtonColor": "#344E41", "ButtonHover": "#588157", "FieldBackColor": "#283618", "FieldForeColor": "#DAD7CD", "HeaderColor": "#011502", "BorderColor": "#656D4A", "CheckColor": "#A3B18A" },
    { "Name": "Desert", "BackColor": "#F0E68C", "ForeColor": "#5D4037", "ButtonColor": "#CD853F", "ButtonHover": "#DAA520", "FieldBackColor": "#FFF8DC", "FieldForeColor": "#8B4513", "HeaderColor": "#8B7D6B", "BorderColor": "#87CEEB", "CheckColor": "#CD853F" },
    { "Name": "Arctic", "BackColor": "#F0FFFF", "ForeColor": "#00008B", "ButtonColor": "#ADD8E6", "ButtonHover": "#B0E0E6", "FieldBackColor": "#FFFFFF", "FieldForeColor": "#000000", "HeaderColor": "#191970", "BorderColor": "#4682B4", "CheckColor": "#191970" },
    { "Name": "Retro 80s", "BackColor": "#D4CFC7", "ForeColor": "#2C2C2C", "ButtonColor": "#A9A9A9", "ButtonHover": "#C0C0C0", "FieldBackColor": "#E6E6E6", "FieldForeColor": "#000000", "HeaderColor": "#5A5A5A", "BorderColor": "#FF4500", "CheckColor": "#A9A9A9" },
    { "Name": "Coffee Shop", "BackColor": "#3B2F2F", "ForeColor": "#F5F5DC", "ButtonColor": "#6F4E37", "ButtonHover": "#8B4513", "FieldBackColor": "#D2B48C", "FieldForeColor": "#362511", "HeaderColor": "#1B1212", "BorderColor": "#A0522D", "CheckColor": "#6F4E37" },
    { "Name": "Sakura Blossom", "BackColor": "#FFF0F5", "ForeColor": "#555555", "ButtonColor": "#FFB6C1", "ButtonHover": "#FFC0CB", "FieldBackColor": "#FFFFFF", "FieldForeColor": "#000000", "HeaderColor": "#DB7093", "BorderColor": "#800020", "CheckColor": "#DB7093" },
    { "Name": "Sunny Day", "BackColor": "#FFFFE0", "ForeColor": "#483C32", "ButtonColor": "#FFD700", "ButtonHover": "#FFA500", "FieldBackColor": "#FFFFFF", "FieldForeColor": "#000000", "HeaderColor": "#87CEEB", "BorderColor": "#FF8C00", "CheckColor": "#FFA500" },
    { "Name": "Futuristic", "BackColor": "#EAEFF2", "ForeColor": "#1A252F", "ButtonColor": "#B0C4DE", "ButtonHover": "#FFFFFF", "FieldBackColor": "#FFFFFF", "FieldForeColor": "#000000", "HeaderColor": "#2F4F4F", "BorderColor": "#778899", "CheckColor": "#4682B4" },
    { "Name": "Cyberpunk", "BackColor": "#0a0a14", "ForeColor": "#E3E3E3", "ButtonColor": "#3D0052", "ButtonHover": "#F0F008", "FieldBackColor": "#1C1C2A", "FieldForeColor": "#08F7FE", "HeaderColor": "#000000", "BorderColor": "#FD5F00", "CheckColor": "#FF0054" },
    { "Name": "Anime", "BackColor": "#F0F8FF", "ForeColor": "#333333", "ButtonColor": "#FFB6C1", "ButtonHover": "#87CEEB", "FieldBackColor": "#FFFFFF", "FieldForeColor": "#5D4037", "HeaderColor": "#4682B4", "BorderColor": "#FF69B4", "CheckColor": "#32CD32" },
    { "Name": "Horror", "BackColor": "#010101", "ForeColor": "#C0C0C0", "ButtonColor": "#300000", "ButtonHover": "#600000", "FieldBackColor": "#121212", "FieldForeColor": "#E0E0E0", "HeaderColor": "#1A0000", "BorderColor": "#444444", "CheckColor": "#FF0000" },
    { "Name": "Blue Neon", "BackColor": "#0A0E27", "ForeColor": "#00F0FF", "ButtonColor": "#1A1F3A", "ButtonHover": "#2D3561", "FieldBackColor": "#0F1629", "FieldForeColor": "#FFFFFF", "HeaderColor": "#050812", "BorderColor": "#00F0FF", "CheckColor": "#FF00FF" },
    { "Name": "Purple Neon", "BackColor": "#1A0A1F", "ForeColor": "#FF00FF", "ButtonColor": "#2D1A3A", "ButtonHover": "#4A2D61", "FieldBackColor": "#140A1A", "FieldForeColor": "#FFFFFF", "HeaderColor": "#0A050F", "BorderColor": "#FF00FF", "CheckColor": "#00FFFF" },
    { "Name": "Green Neon", "BackColor": "#0A1F0A", "ForeColor": "#00FF00", "ButtonColor": "#1A3A1A", "ButtonHover": "#2D612D", "FieldBackColor": "#0F1A0F", "FieldForeColor": "#FFFFFF", "HeaderColor": "#050F05", "BorderColor": "#00FF00", "CheckColor": "#FFFF00" },
    { "Name": "Amber Glow", "BackColor": "#1F1A0A", "ForeColor": "#FFA500", "ButtonColor": "#3A2D1A", "ButtonHover": "#61492D", "FieldBackColor": "#1A140A", "FieldForeColor": "#FFD700", "HeaderColor": "#0F0A05", "BorderColor": "#FFA500", "CheckColor": "#FF0000" },
    { "Name": "Rainbow Neon", "BackColor": "#0A0A0A", "ForeColor": "#00FFFF", "ButtonColor": "#1F1A2D", "ButtonHover": "#3A2D4A", "FieldBackColor": "#0F0F14", "FieldForeColor": "#FFFFFF", "HeaderColor": "#05010A", "BorderColor": "#00FF00", "CheckColor": "#FFA500" },
    { "Name": "Cyberpunk Neon", "BackColor": "#0D0221", "ForeColor": "#00FFFF", "ButtonColor": "#260F3A", "ButtonHover": "#FF00FF", "FieldBackColor": "#0F1629", "FieldForeColor": "#FFFFFF", "HeaderColor": "#05010A", "BorderColor": "#FF00FF", "CheckColor": "#39FF14" },
    { "Name": "Neon Sunset", "BackColor": "#240046", "ForeColor": "#FF9100", "ButtonColor": "#FF007F", "ButtonHover": "#FF79B4", "FieldBackColor": "#3C096C", "FieldForeColor": "#FFFF00", "HeaderColor": "#10002B", "BorderColor": "#FFFF00", "CheckColor": "#FF007F" },
    { "Name": "Neon Galaxy", "BackColor": "#000000", "ForeColor": "#00BFFF", "ButtonColor": "#191970", "ButtonHover": "#FFD700", "FieldBackColor": "#1A1A1A", "FieldForeColor": "#FFFFFF", "HeaderColor": "#010101", "BorderColor": "#00BFFF", "CheckColor": "#FFD700" },
    { "Name": "Toxic Neon", "BackColor": "#0A1F0A", "ForeColor": "#39FF14", "ButtonColor": "#2D1A3A", "ButtonHover": "#9D00FF", "FieldBackColor": "#000000", "FieldForeColor": "#FFFF00", "HeaderColor": "#050F05", "BorderColor": "#9D00FF", "CheckColor": "#39FF14" },
    { "Name": "Electric Ocean", "BackColor": "#022B3A", "ForeColor": "#20B2AA", "ButtonColor": "#000080", "ButtonHover": "#FF7F50", "FieldBackColor": "#01161E", "FieldForeColor": "#FFFFFF", "HeaderColor": "#000D11", "BorderColor": "#FF7F50", "CheckColor": "#7FFFD4" },
    { "Name": "Fiery Neon", "BackColor": "#2B0000", "ForeColor": "#FF0000", "ButtonColor": "#8B4000", "ButtonHover": "#FF4500", "FieldBackColor": "#000000", "FieldForeColor": "#FFFF00", "HeaderColor": "#150000", "BorderColor": "#FF4500", "CheckColor": "#FFFF00" },
    { "Name": "Retrowave", "BackColor": "#10102A", "ForeColor": "#FF007F", "ButtonColor": "#4B0082", "ButtonHover": "#00FFFF", "FieldBackColor": "#0A0A1A", "FieldForeColor": "#FFFFE0", "HeaderColor": "#000000", "BorderColor": "#00FFFF", "CheckColor": "#FF007F" },
    { "Name": "Ghost Neon", "BackColor": "#121212", "ForeColor": "#F8F8FF", "ButtonColor": "#483D8B", "ButtonHover": "#B0C4DE", "FieldBackColor": "#000000", "FieldForeColor": "#FFFFFF", "HeaderColor": "#080808", "BorderColor": "#98FB98", "CheckColor": "#B0C4DE" },
    { "Name": "Candy Neon", "BackColor": "#1D0C26", "ForeColor": "#FF69B4", "ButtonColor": "#00A7E1", "ButtonHover": "#90EE90", "FieldBackColor": "#311432", "FieldForeColor": "#FFFACD", "HeaderColor": "#0E0613", "BorderColor": "#00A7E1", "CheckColor": "#FF69B4" },
    { "Name": "Plasma Neon", "BackColor": "#000000", "ForeColor": "#00FF7F", "ButtonColor": "#8A2BE2", "ButtonHover": "#FF1493", "FieldBackColor": "#000033", "FieldForeColor": "#FFFFFF", "HeaderColor": "#00001A", "BorderColor": "#FF1493", "CheckColor": "#00FF7F" },
    
    # --- ULTRA THEMES (Gradient / Animated Feel) ---
    { 
        "Name": "Cyber Prime (ULTRA)", 
        "BackColor": "#0d1117", 
        "ForeColor": "#c9d1d9", 
        "ButtonColor": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1f6feb, stop:1 #114899)", 
        "ButtonHover": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #388bfd, stop:1 #1f6feb)", 
        "FieldBackColor": "#161b22", 
        "FieldForeColor": "#FFFFFF", 
        "HeaderColor": "#0d1117", 
        "BorderColor": "#30363d", 
        "CheckColor": "#1f6feb" 
    },
    { 
        "Name": "Golden Luxury (ULTRA)", 
        "BackColor": "#1a1a1a", 
        "ForeColor": "#e6c200", 
        "ButtonColor": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffd700, stop:1 #b8860b)", 
        "ButtonHover": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffed4a, stop:1 #daa520)", 
        "FieldBackColor": "#2c2c2c", 
        "FieldForeColor": "#ffd700", 
        "HeaderColor": "#000000", 
        "BorderColor": "#b8860b", 
        "CheckColor": "#ffd700" 
    },
    { 
        "Name": "Neon Flux (ULTRA)", 
        "BackColor": "#050510", 
        "ForeColor": "#00ffff", 
        "ButtonColor": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff00ff, stop:1 #00ffff)", 
        "ButtonHover": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff55ff, stop:1 #55ffff)", 
        "FieldBackColor": "#0a0a20", 
        "FieldForeColor": "#ffffff", 
        "HeaderColor": "#020205", 
        "BorderColor": "#ff00ff", 
        "CheckColor": "#00ffff" 
    },
    { 
        "Name": "Inferno Blaze (ULTRA)", 
        "BackColor": "#1a0505", 
        "ForeColor": "#ffaa00", 
        "ButtonColor": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff4500, stop:1 #8b0000)", 
        "ButtonHover": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff6347, stop:1 #a52a2a)", 
        "FieldBackColor": "#2e0a0a", 
        "FieldForeColor": "#ffcc00", 
        "HeaderColor": "#1a0505", 
        "BorderColor": "#ff4500", 
        "CheckColor": "#ff8c00" 
    },
    { 
        "Name": "Arctic Aurora (ULTRA)", 
        "BackColor": "#0b1021", 
        "ForeColor": "#88c0d0", 
        "ButtonColor": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #81a1c1, stop:1 #5e81ac)", 
        "ButtonHover": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8fbcbb, stop:1 #81a1c1)", 
        "FieldBackColor": "#2e3440", 
        "FieldForeColor": "#eceff4", 
        "HeaderColor": "#0b1021", 
        "BorderColor": "#81a1c1", 
        "CheckColor": "#a3be8c" 
    },
    { 
        "Name": "Deep Void (ULTRA)", 
        "BackColor": "#000000", 
        "ForeColor": "#ffffff", 
        "ButtonColor": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #333333, stop:1 #000000)", 
        "ButtonHover": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #555555, stop:1 #222222)", 
        "FieldBackColor": "#111111", 
        "FieldForeColor": "#cccccc", 
        "HeaderColor": "#000000", 
        "BorderColor": "#444444", 
        "CheckColor": "#ffffff" 
    },
    { 
        "Name": "Matrix Code (ULTRA)", 
        "BackColor": "#000500", 
        "ForeColor": "#00ff00", 
        "ButtonColor": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #003300, stop:1 #001100)", 
        "ButtonHover": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #005500, stop:1 #002200)", 
        "FieldBackColor": "#001100", 
        "FieldForeColor": "#00ff00", 
        "HeaderColor": "#000000", 
        "BorderColor": "#004400", 
        "CheckColor": "#00ff00" 
    },
    { 
        "Name": "Royal Velvet (ULTRA)", 
        "BackColor": "#1a0b1e", 
        "ForeColor": "#d8b4e2", 
        "ButtonColor": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6a0572, stop:1 #39065a)", 
        "ButtonHover": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #890999, stop:1 #52097a)", 
        "FieldBackColor": "#2d1235", 
        "FieldForeColor": "#eaccee", 
        "HeaderColor": "#1a0b1e", 
        "BorderColor": "#6a0572", 
        "CheckColor": "#d8b4e2" 
    },
    { 
        "Name": "Sunset Retro (ULTRA)", 
        "BackColor": "#2d1b4e", 
        "ForeColor": "#f0fff1", 
        "ButtonColor": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffd319, stop:1 #ff2975)", 
        "ButtonHover": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffea61, stop:1 #ff4f8b)", 
        "FieldBackColor": "#1f0c29", 
        "FieldForeColor": "#ffffff", 
        "HeaderColor": "#2d1b4e", 
        "BorderColor": "#ff2975", 
        "CheckColor": "#8c1eff" 
    },
    { 
        "Name": "Toxic Hazard (ULTRA)", 
        "BackColor": "#0d140d", 
        "ForeColor": "#ccff00", 
        "ButtonColor": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #66ff33, stop:1 #339900)", 
        "ButtonHover": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #88ff66, stop:1 #44cc00)", 
        "FieldBackColor": "#1a261a", 
        "FieldForeColor": "#ccff00", 
        "HeaderColor": "#0d140d", 
        "BorderColor": "#66ff33", 
        "CheckColor": "#ccff00" 
    }
]
