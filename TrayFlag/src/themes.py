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