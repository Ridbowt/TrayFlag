# File: src/themes.py

def get_context_menu_style():
    """
    Returns a stylesheet for customizing QMenu.
    """
    menu_bg_color = "#2D2D2D"      # Our graphite color
    text_color = "#F0F0F0"         # Light text
    selection_color = "#005A9C"   # Blue for selection
    separator_color = "#606060"    # Separator color

    # --- NEW COLOR FOR INACTIVE TEXT ---
    disabled_text_color = "#909090" # Light gray, but darker than the main one

    return f"""
        QMenu {{
            background-color: {menu_bg_color};
            color: {text_color};
            border: 1px solid {separator_color};
            padding: 5px;
        }}
        QMenu::item {{
            padding: 5px 25px 5px 25px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {selection_color};
        }}
        
        /* --- BEGIN OF NEW BLOCK --- */
        QMenu::item:disabled {{
            color: {disabled_text_color};
            background-color: transparent; /* Make sure the background does not change */
        }}
        /* --- END OF NEW BLOCK --- */

        QMenu::separator {{
            height: 1px;
            background: {separator_color};
            margin-left: 10px;
            margin-right: 10px;
        }}
    """

def get_about_dialog_style():
    """
    Returns the style for the "About" window with a graphite background.
    """
    dialog_bg_color = "#2D2D2D"
    text_color = "#F0F0F0"
    border_color = "#606060"

    return f"""
        /* Apply the style only to QDialog with objectName='aboutDialog' */
        QDialog#aboutDialog {{
            background-color: {dialog_bg_color};
        }}
        /* Apply the style to child elements only within this dialog */
        QDialog#aboutDialog QLabel, 
        QDialog#aboutDialog QGroupBox {{
            color: {text_color};
            background-color: transparent;
        }}
        QDialog#aboutDialog QGroupBox {{
            border: 1px solid {border_color};
            border-radius: 5px;
            margin-top: 0.5em;
        }}
        QDialog#aboutDialog QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }}
    """

# Dictionary with palettes for buttons. All colors are stored here.
BUTTON_PALETTES = {
    "ok": {
        "bg": "#3399FF",
        "hover": "#44aaff",
        "pressed": "#2288ee",
        "border": "#555"
    },
    "cancel": {
        "bg": "#777777",
        "hover": "#888888",
        "pressed": "#666666",
        "border": "#555"
    },
    "info": {
        "bg": "#4488AA",
        "hover": "#5599bb",
        "pressed": "#337799",
        "border": "#337799"
    },
    "update": {
        "bg": "#28A745",      # Nice green
        "hover": "#218838",   # Slightly darker on hover
        "pressed": "#1E7E34", # Even darker when pressed
        "border": "#28A745"
    }
}

def get_button_style(button_type):
    """
    Returns the ready stylesheet string for the button.
    button_type can be 'ok', 'cancel', 'info'
    """
    palette = BUTTON_PALETTES.get(button_type, BUTTON_PALETTES['cancel'])
    
    return f"""
        QPushButton {{
            background-color: {palette['bg']};
            color: white;
            border: 1px solid {palette['border']};
            padding: 5px 15px;
            border-radius: 3px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {palette['hover']};
        }}
        QPushButton:pressed {{
            background-color: {palette['pressed']};
        }}
    """

def get_settings_dialog_style():
    """
    Returns the style for the "Settings" window.
    """
    dialog_bg_color = "#2D2D2D"
    text_color = "#F0F0F0"
    border_color = "#606060"

    return f"""
        /* Apply the style only to QDialog with objectName='settingsDialog' */
        QDialog#settingsDialog {{
            background-color: {dialog_bg_color};
        }}
        /* Styles for child elements */
        QDialog#settingsDialog QWidget, /* Important for tabs */
        QDialog#settingsDialog QLabel, 
        QDialog#settingsDialog QGroupBox,
        QDialog#settingsDialog QCheckBox,
        QDialog#settingsDialog QRadioButton,
        QDialog#settingsDialog QSpinBox,
        QDialog#settingsDialog QComboBox {{
            color: {text_color};
            background-color: transparent;
        }}
        QDialog#settingsDialog QGroupBox {{
            border: 1px solid {border_color};
            border-radius: 5px;
            margin-top: 0.5em;
        }}
        QDialog#settingsDialog QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }}
        /* Styles for tabs */
        QDialog#settingsDialog QTabBar::tab {{
            color: {text_color};
            background-color: #555555;
            padding: 5px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        QDialog#settingsDialog QTabBar::tab:selected {{
            background-color: {dialog_bg_color};
        }}
        QDialog#settingsDialog QTabWidget::pane {{
            border: 1px solid {border_color};
        }}
    """
