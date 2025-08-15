# File: src/dialogs.py
import os
from PySide6 import QtWidgets, QtGui, QtCore
from utils import resource_path
from constants import APP_NAME
import themes

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, app_icon, tr, version, release_date, logo_pixmap, parent=None):
        super().__init__(parent)
        self.setObjectName("aboutDialog")
        self.setStyleSheet(themes.get_about_dialog_style())
        self.tr = tr
        
        self.setWindowTitle(self.tr.get("about_dialog_title", app_name=APP_NAME))
        self.setWindowIcon(app_icon)
        self.setFixedSize(610, 397)

        layout = QtWidgets.QVBoxLayout(self)
        
        # --- НОВЫЙ БЛОК: Создаем "шапку" с горизонтальной компоновкой ---
        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0) # Убираем лишние отступы

        # Левая часть шапки: Логотип
        logo_label = QtWidgets.QLabel()
        if logo_pixmap:
            logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        logo_label.setContentsMargins(10, 0, 20, 0) # Отступы справа от лого

        # Правая часть шапки: Название, версия, сайт
        title_widget = QtWidgets.QWidget()
        title_layout = QtWidgets.QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2) # Уменьшаем расстояние между строками

        title_label = QtWidgets.QLabel(f"<b>{APP_NAME}</b>")
        font = title_label.font(); font.setPointSize(14); title_label.setFont(font)
        
        version_label = QtWidgets.QLabel(self.tr.get("about_version", version=version, release_date=release_date))
        
        website_label = QtWidgets.QLabel(f'<a href="https://github.com/Ridbowt/TrayFlag">{self.tr.get("about_website")}</a>')
        website_label.setOpenExternalLinks(True)

        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        title_layout.addWidget(website_label)
        title_layout.addStretch() # Прижимает текст к верху

        # Добавляем логотип и текст в шапку
        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_widget)
        # --- КОНЕЦ БЛОКА "ШАПКИ" ---

        # --- Остальные виджеты (без изменений) ---
        acknowledgements_box = QtWidgets.QGroupBox(self.tr.get("about_acknowledgements"))
        ack_layout = QtWidgets.QVBoxLayout()
        ack_layout.setContentsMargins(5, 10, 5, 5)
        ack_layout.setSpacing(5)
        
        ack_keys = ['ip_services', 'flags', 'app_icon', 'logo_builder', 'sound', 'code', 'ai']
        line_color = "#606060"
        for i, key in enumerate(ack_keys):
            line_label = QtWidgets.QLabel(self.tr.get(f'ack_{key}'))
            line_label.setTextFormat(QtCore.Qt.TextFormat.RichText)
            line_label.setOpenExternalLinks(True)
            line_label.setWordWrap(True)
            ack_layout.addWidget(line_label)
            if i < len(ack_keys) - 1:
                line = QtWidgets.QFrame(); line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
                line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken); line.setStyleSheet(f"background-color: {line_color};"); line.setFixedHeight(1)
                ack_layout.addWidget(line)
        acknowledgements_box.setLayout(ack_layout)
        
        button_box = QtWidgets.QDialogButtonBox()
        ok_button = button_box.addButton(self.tr.get("button_ok"), QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        ok_color = "#4488AA"
        ok_button.setStyleSheet(f"QPushButton {{ background-color: {ok_color}; color: white; border: 1px solid #337799; padding: 5px 15px; border-radius: 3px; font-weight: bold; }} QPushButton:hover {{ background-color: #5599bb; }} QPushButton:pressed {{ background-color: #337799; }}")
        button_box.accepted.connect(self.accept)

        # --- Добавляем все блоки в главную ВЕРТИКАЛЬНУЮ компоновку ---
        layout.addWidget(header_widget)
        layout.addWidget(acknowledgements_box)
        layout.addStretch()
        layout.addWidget(button_box)
    # --- КОНЕЦ КОДА ДЛЯ ЗАМЕНЫ ---

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, app_icon, tr, available_langs, current_config, parent=None):
        super().__init__(parent)
        self.tr = tr
        self.setWindowTitle(tr.get("settings_dialog_title", app_name=APP_NAME))
        self.setWindowIcon(app_icon)
        
        layout = QtWidgets.QVBoxLayout(self)
        tabs = QtWidgets.QTabWidget()
        general_tab = QtWidgets.QWidget()
        idle_tab = QtWidgets.QWidget()
        tabs.addTab(general_tab, self.tr.get("settings_tab_general"))
        tabs.addTab(idle_tab, self.tr.get("settings_tab_idle"))
        layout.addWidget(tabs)

        # --- General Tab ---
        general_layout = QtWidgets.QFormLayout(general_tab)
        self.language_combo = QtWidgets.QComboBox()
        for code, name in available_langs.items(): self.language_combo.addItem(name, code)
        # --- ВОЗВРАЩАЕМ СТАРУЮ, РАБОЧУЮ ЛОГИКУ ---
        current_lang_code = current_config.language
        # Ищем индекс элемента, чьи "скрытые данные" (код языка) нам нужны
        index = self.language_combo.findData(current_lang_code)
        if index != -1: # findData возвращает -1, если ничего не найдено
            self.language_combo.setCurrentIndex(index)
        # --- КОНЕЦ ИСПРАВЛЕННОГО БЛОКА ---
        general_layout.addRow(tr.get("settings_language"), self.language_combo)
        self.update_interval_spinbox = QtWidgets.QSpinBox()
        self.update_interval_spinbox.setMinimum(4); self.update_interval_spinbox.setMaximum(300); self.update_interval_spinbox.setSuffix(" s")
        self.update_interval_spinbox.setValue(current_config.update_interval)
        general_layout.addRow(tr.get("settings_update_interval"), self.update_interval_spinbox)
        self.autostart_checkbox = QtWidgets.QCheckBox(tr.get("settings_autostart")); self.autostart_checkbox.setChecked(current_config.autostart); general_layout.addRow(self.autostart_checkbox)
        self.notifications_checkbox = QtWidgets.QCheckBox(tr.get("settings_notifications")); self.notifications_checkbox.setChecked(current_config.notifications); general_layout.addRow(self.notifications_checkbox)
        self.sound_checkbox = QtWidgets.QCheckBox(tr.get("settings_sound")); self.sound_checkbox.setChecked(current_config.sound); general_layout.addRow(self.sound_checkbox)

                # --- НАЧАЛО НОВОГО КОДА ---
        # Создаем группу для радио-кнопок громкости
        self.volume_groupbox = QtWidgets.QGroupBox(self.tr.get("settings_volume_level"))
        volume_layout = QtWidgets.QHBoxLayout() # Горизонтальная компоновка
        self.volume_groupbox.setLayout(volume_layout)

        # Создаем сами радио-кнопки
        self.volume_low_rb = QtWidgets.QRadioButton(self.tr.get("volume_low"))
        self.volume_medium_rb = QtWidgets.QRadioButton(self.tr.get("volume_medium"))
        self.volume_high_rb = QtWidgets.QRadioButton(self.tr.get("volume_high"))

        # Добавляем их в компоновку
        volume_layout.addWidget(self.volume_low_rb)
        volume_layout.addWidget(self.volume_medium_rb)
        volume_layout.addWidget(self.volume_high_rb)

        # Устанавливаем текущее значение
        if current_config.volume_level == "low":
            self.volume_low_rb.setChecked(True)
        elif current_config.volume_level == "high":
            self.volume_high_rb.setChecked(True)
        else: # medium по умолчанию
            self.volume_medium_rb.setChecked(True)
        
        general_layout.addRow(self.volume_groupbox)

        # Логика включения/выключения группы
        self.sound_checkbox.toggled.connect(self.volume_groupbox.setEnabled)
        self.volume_groupbox.setEnabled(current_config.sound)
        # --- КОНЕЦ НОВОГО КОДА ---

        # --- Idle Mode Tab ---
        idle_layout = QtWidgets.QVBoxLayout(idle_tab)
        self.idle_enabled_checkbox = QtWidgets.QCheckBox(self.tr.get("settings_idle_enable")); self.idle_enabled_checkbox.setChecked(current_config.idle_enabled); idle_layout.addWidget(self.idle_enabled_checkbox)
        self.idle_options_widget = QtWidgets.QWidget()
        idle_form_layout = QtWidgets.QFormLayout(self.idle_options_widget)
        self.idle_threshold_spinbox = QtWidgets.QSpinBox()
        self.idle_threshold_spinbox.setMinimum(1); self.idle_threshold_spinbox.setMaximum(120); self.idle_threshold_spinbox.setSuffix(f" {self.tr.get('minutes')}")
        self.idle_threshold_spinbox.setValue(current_config.idle_threshold_mins)
        idle_form_layout.addRow(self.tr.get("settings_idle_threshold"), self.idle_threshold_spinbox)
        self.idle_interval_spinbox = QtWidgets.QSpinBox()
        self.idle_interval_spinbox.setMinimum(1); self.idle_interval_spinbox.setMaximum(180); self.idle_interval_spinbox.setSuffix(f" {self.tr.get('minutes')}")
        self.idle_interval_spinbox.setValue(current_config.idle_interval_mins)
        idle_form_layout.addRow(self.tr.get("settings_idle_interval"), self.idle_interval_spinbox)
        idle_layout.addWidget(self.idle_options_widget); idle_layout.addStretch()
        self.idle_enabled_checkbox.toggled.connect(self.idle_options_widget.setEnabled)
        self.idle_options_widget.setEnabled(current_config.idle_enabled)

        # --- Buttons ---
        button_box = QtWidgets.QDialogButtonBox()
        ok_button = button_box.addButton(self.tr.get("button_ok"), QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_button = button_box.addButton(self.tr.get("button_cancel"), QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        ok_color = "#3399FF"; cancel_color = "#777777"
        ok_button.setStyleSheet(f"QPushButton {{ background-color: {ok_color}; color: white; border: 1px solid #555; padding: 5px 15px; border-radius: 3px; font-weight: bold; }} QPushButton:hover {{ background-color: #44aaff; }} QPushButton:pressed {{ background-color: #2288ee; }}")
        cancel_button.setStyleSheet(f"QPushButton {{ background-color: {cancel_color}; color: white; border: 1px solid #555; padding: 5px 15px; border-radius: 3px; }} QPushButton:hover {{ background-color: #888888; }} QPushButton:pressed {{ background-color: #666666; }}")
        button_box.accepted.connect(self.accept); button_box.rejected.connect(self.reject); layout.addWidget(button_box)

    def get_settings(self):
                # --- НАЧАЛО НОВОГО КОДА ---
        volume_level = "medium"
        if self.volume_low_rb.isChecked():
            volume_level = "low"
        elif self.volume_high_rb.isChecked():
            volume_level = "high"
        # --- КОНЕЦ НОВОГО КОДА ---
        return {
            'language': self.language_combo.currentData(), 'update_interval': self.update_interval_spinbox.value(),
            'autostart': self.autostart_checkbox.isChecked(), 'notifications': self.notifications_checkbox.isChecked(),
            'sound': self.sound_checkbox.isChecked(), 'idle_enabled': self.idle_enabled_checkbox.isChecked(), 'volume_level': volume_level,
            'idle_threshold_mins': self.idle_threshold_spinbox.value(), 'idle_interval_mins': self.idle_interval_spinbox.value(),
        }