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
        self.setFixedSize(693, 406)

        main_layout = QtWidgets.QHBoxLayout(self)
        
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Мы больше не грузим картинку, а просто используем ту, что нам передали
        logo_label = QtWidgets.QLabel()
        if logo_pixmap:
            logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter)
        logo_label.setContentsMargins(10, 10, 10, 10)
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---
        
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        
        title_label = QtWidgets.QLabel(f"<b>{APP_NAME}</b>")
        font = title_label.font(); font.setPointSize(14); title_label.setFont(font)
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        
        version_label = QtWidgets.QLabel(self.tr.get("about_version", version=version, release_date=release_date))
        version_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        
        website_label = QtWidgets.QLabel(f'<a href="https://github.com/Ridbowt/TrayFlag">{self.tr.get("about_website")}</a>')
        website_label.setOpenExternalLinks(True)
        website_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        
        # ...
        acknowledgements_box = QtWidgets.QGroupBox(self.tr.get("about_acknowledgements"))
        ack_layout = QtWidgets.QVBoxLayout()
        ack_layout.setContentsMargins(5, 10, 5, 5) # Немного увеличим отступы для красоты
        ack_layout.setSpacing(5) # Задаем расстояние между виджетами

        # --- НАЧАЛО НОВОЙ ЛОГИКИ ---
        
        # Список ключей для благодарностей
        ack_keys = ['ip_services', 'flags', 'app_icon', 'logo_builder', 'sound', 'code', 'ai']
        
        # Цвет для линии, такой же, как у рамки
        line_color = "#606060"

        for i, key in enumerate(ack_keys):
            # Создаем QLabel для каждой строки благодарности
            line_label = QtWidgets.QLabel(self.tr.get(f'ack_{key}'))
            line_label.setTextFormat(QtCore.Qt.TextFormat.RichText)
            line_label.setOpenExternalLinks(True)
            line_label.setWordWrap(True)
            ack_layout.addWidget(line_label)

            # Добавляем линию-разделитель после каждого пункта, кроме последнего
            if i < len(ack_keys) - 1:
                line = QtWidgets.QFrame()
                line.setFrameShape(QtWidgets.QFrame.Shape.HLine) # Горизонтальная линия
                line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
                # Устанавливаем цвет линии
                line.setStyleSheet(f"background-color: {line_color};")
                line.setFixedHeight(1) # Высота в 1 пиксель
                ack_layout.addWidget(line)

        acknowledgements_box.setLayout(ack_layout)
        # --- КОНЕЦ НОВОЙ ЛОГИКИ ---
        # ...
        
        button_box = QtWidgets.QDialogButtonBox()
        ok_button = button_box.addButton(self.tr.get("button_ok"), QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        ok_color = "#4488AA"
        ok_button.setStyleSheet(f"QPushButton {{ background-color: {ok_color}; color: white; border: 1px solid #337799; padding: 5px 15px; border-radius: 3px; font-weight: bold; }} QPushButton:hover {{ background-color: #5599bb; }} QPushButton:pressed {{ background-color: #337799; }}")
        button_box.accepted.connect(self.accept)

        right_layout.addWidget(title_label); right_layout.addWidget(version_label); right_layout.addWidget(website_label)
        right_layout.addSpacing(15); right_layout.addWidget(acknowledgements_box); right_layout.addStretch(); right_layout.addWidget(button_box)
        main_layout.addWidget(logo_label); main_layout.addWidget(right_widget)

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
        return {
            'language': self.language_combo.currentData(), 'update_interval': self.update_interval_spinbox.value(),
            'autostart': self.autostart_checkbox.isChecked(), 'notifications': self.notifications_checkbox.isChecked(),
            'sound': self.sound_checkbox.isChecked(), 'idle_enabled': self.idle_enabled_checkbox.isChecked(),
            'idle_threshold_mins': self.idle_threshold_spinbox.value(), 'idle_interval_mins': self.idle_interval_spinbox.value(),
        }