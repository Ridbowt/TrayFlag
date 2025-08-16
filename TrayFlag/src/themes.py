# File: src/themes.py

def get_context_menu_style():
    """
    Возвращает stylesheet для кастомизации QMenu.
    """
    menu_bg_color = "#2D2D2D"      # Наш графитовый цвет
    text_color = "#F0F0F0"         # Светлый текст
    selection_color = "#005A9C"   # Cиний для выделения
    separator_color = "#606060"    # Цвет разделителя

    # --- НОВЫЙ ЦВЕТ ДЛЯ НЕАКТИВНОГО ТЕКСТА ---
    disabled_text_color = "#909090" # Светло-серый, но темнее основного

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
        
        /* --- НАЧАЛО НОВОГО БЛОКА --- */
        QMenu::item:disabled {{
            color: {disabled_text_color};
            background-color: transparent; /* Убедимся, что фон не меняется */
        }}
        /* --- КОНЕЦ НОВОГО БЛОКА --- */

        QMenu::separator {{
            height: 1px;
            background: {separator_color};
            margin-left: 10px;
            margin-right: 10px;
        }}
    """

def get_about_dialog_style():
    """
    Возвращает стиль для окна "О программе" с графитовым фоном.
    """
    dialog_bg_color = "#2D2D2D"
    text_color = "#F0F0F0"
    border_color = "#606060"

    return f"""
        /* Применяем стиль только к QDialog, у которого есть свойство objectName='aboutDialog' */
        QDialog#aboutDialog {{
            background-color: {dialog_bg_color};
        }}
        /* Применяем стиль к дочерним элементам только внутри этого диалога */
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

# --- ДОБАВЬТЕ ЭТОТ КОД В КОНЕЦ ФАЙЛА themes.py ---

# Словарь с палитрами для кнопок. Все цвета хранятся здесь.
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
    }
}

def get_button_style(button_type):
    """
    Возвращает готовую строку stylesheet для кнопки.
    button_type может быть 'ok', 'cancel', 'info'.
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
    Возвращает стиль для окна "Настройки".
    """
    dialog_bg_color = "#2D2D2D"
    text_color = "#F0F0F0"
    border_color = "#606060"

    return f"""
        /* Применяем стиль только к QDialog с objectName='settingsDialog' */
        QDialog#settingsDialog {{
            background-color: {dialog_bg_color};
        }}
        /* Стили для дочерних элементов */
        QDialog#settingsDialog QWidget, /* Важно для вкладок */
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
        /* Стиль для вкладок */
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