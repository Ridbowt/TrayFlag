# File: src/dialogs.py

import os
import webbrowser
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
        self.setFixedSize(624, 425)

        layout = QtWidgets.QVBoxLayout(self)
        
        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        logo_label = QtWidgets.QLabel()
        if logo_pixmap:
            logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        logo_label.setContentsMargins(10, 0, 20, 0)

        title_widget = QtWidgets.QWidget()
        title_layout = QtWidgets.QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)

        title_label = QtWidgets.QLabel(f"<b>{APP_NAME}</b>")
        font = title_label.font(); font.setPointSize(14); title_label.setFont(font)
        
        version_label = QtWidgets.QLabel(self.tr.get("about_version", version=version, release_date=release_date))
        
        website_label = QtWidgets.QLabel(f'⭐ <a href="https://github.com/Ridbowt/TrayFlag">{self.tr.get("about_website")}</a>')
        website_label.setOpenExternalLinks(True)

        telegram_label = QtWidgets.QLabel(f'✈️ <a href="https://t.me/trayflag">{self.tr.get("about_telegram")}</a>')
        telegram_label.setOpenExternalLinks(True)

        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        title_layout.addWidget(website_label)
        title_layout.addWidget(telegram_label)
        title_layout.addStretch()

        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_widget)

# --- START OF NEW TAB BLOCK ---
        
        # Create a container for tabs
        tabs = QtWidgets.QTabWidget()

        # --- TAB 1: Acknowledgements ---
        acknowledgements_widget = QtWidgets.QWidget()
        ack_layout = QtWidgets.QVBoxLayout(acknowledgements_widget)
        ack_layout.setContentsMargins(10, 10, 10, 10)
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
        
        # --- TAB 2: Sponsors ---
        sponsors_widget = QtWidgets.QWidget()
        sponsors_layout = QtWidgets.QVBoxLayout(sponsors_widget)
        
        sponsors_text = QtWidgets.QTextEdit()
        sponsors_text.setReadOnly(True)
        
        # Attempt to load the list of sponsors from a file
        try:
            sponsors_file_path = resource_path(os.path.join("assets", "sponsors.txt"))
            with open(sponsors_file_path, 'r', encoding='utf-8') as f:
                # Read all lines, removing empty ones and extra spaces
                sponsors_list = [line.strip() for line in f if line.strip()]
            
            if sponsors_list:
                sponsors_text.setPlainText("\n".join(sponsors_list))
            else:
                # If the file is empty
                sponsors_text.setPlainText(self.tr.get("sponsors_list_empty"))
        except FileNotFoundError:
            # If the file doesn't exist
            sponsors_text.setPlainText(self.tr.get("sponsors_list_empty"))
        except Exception as e:
            # If there's any other error
            sponsors_text.setPlainText(self.tr.get("sponsors_list_error"))
            print(f"Error loading sponsors.txt: {e}") # Для отладки
        
        sponsors_layout.addWidget(sponsors_text)

        # Add tabs to the tab widget
        tabs.addTab(acknowledgements_widget, self.tr.get("about_tab_acknowledgements"))
        tabs.addTab(sponsors_widget, self.tr.get("about_tab_sponsors"))

        # --- ЕND OF NEW TAB BLOCK ---

        bottom_panel = QtWidgets.QWidget()
        buttons_layout = QtWidgets.QHBoxLayout(bottom_panel)
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        # --- Boosty Button (Left) ---
        boosty_button = QtWidgets.QPushButton(self.tr.get("button_support_on_boosty"))
        boosty_color = "#F15F2C"; boosty_hover_color = "#FF7F4C"
        boosty_button.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {boosty_color}; color: white; border: none; 
                padding: 5px 15px; border-radius: 3px; font-weight: bold; 
            }}
            QPushButton:hover {{ background-color: {boosty_hover_color}; }}
        """)
        boosty_button.clicked.connect(lambda: webbrowser.open("https://boosty.to/trayflag"))
        
        ok_button = QtWidgets.QPushButton(self.tr.get("button_ok"))
        ok_button.setStyleSheet(themes.get_button_style("info"))
        ok_button.clicked.connect(self.accept)

        buttons_layout.addWidget(boosty_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok_button)

        layout.addWidget(header_widget)
        layout.addWidget(tabs)
        layout.addStretch()
        layout.addWidget(bottom_panel)

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

        general_layout = QtWidgets.QFormLayout(general_tab)
        self.language_combo = QtWidgets.QComboBox()
        for code, name in available_langs.items(): self.language_combo.addItem(name, code)

        current_lang_code = current_config.language

        index = self.language_combo.findData(current_lang_code)
        if index != -1:
            self.language_combo.setCurrentIndex(index)

        general_layout.addRow(tr.get("settings_language"), self.language_combo)
        self.update_interval_spinbox = QtWidgets.QSpinBox()
        self.update_interval_spinbox.setMinimum(4); self.update_interval_spinbox.setMaximum(300); self.update_interval_spinbox.setSuffix(" s")
        self.update_interval_spinbox.setValue(current_config.update_interval)
        general_layout.addRow(tr.get("settings_update_interval"), self.update_interval_spinbox)
        self.autostart_checkbox = QtWidgets.QCheckBox(tr.get("settings_autostart")); self.autostart_checkbox.setChecked(current_config.autostart); general_layout.addRow(self.autostart_checkbox)
        self.notifications_checkbox = QtWidgets.QCheckBox(tr.get("settings_notifications")); self.notifications_checkbox.setChecked(current_config.notifications); general_layout.addRow(self.notifications_checkbox)

        self.sound_checkbox = QtWidgets.QCheckBox(tr.get("settings_sound")); self.sound_checkbox.setChecked(current_config.sound); general_layout.addRow(self.sound_checkbox)

        self.volume_groupbox = QtWidgets.QGroupBox(self.tr.get("settings_volume_level"))
        volume_layout = QtWidgets.QHBoxLayout()
        self.volume_groupbox.setLayout(volume_layout)

        self.volume_low_rb = QtWidgets.QRadioButton(self.tr.get("volume_low"))
        self.volume_medium_rb = QtWidgets.QRadioButton(self.tr.get("volume_medium"))
        self.volume_high_rb = QtWidgets.QRadioButton(self.tr.get("volume_high"))

        volume_layout.addWidget(self.volume_low_rb)
        volume_layout.addWidget(self.volume_medium_rb)
        volume_layout.addWidget(self.volume_high_rb)

        if current_config.volume_level == "low":
            self.volume_low_rb.setChecked(True)
        elif current_config.volume_level == "high":
            self.volume_high_rb.setChecked(True)
        else:
            self.volume_medium_rb.setChecked(True)
        
        general_layout.addRow(self.volume_groupbox)

        self.sound_checkbox.toggled.connect(self.volume_groupbox.setEnabled)
        self.volume_groupbox.setEnabled(current_config.sound)

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

        button_box = QtWidgets.QDialogButtonBox(self)
        ok_button = button_box.addButton(self.tr.get("button_ok"), QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_button = button_box.addButton(self.tr.get("button_cancel"), QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        
        ok_button.setStyleSheet(themes.get_button_style("ok"))
        cancel_button.setStyleSheet(themes.get_button_style("cancel"))
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_settings(self):
        volume_level = "medium"
        if self.volume_low_rb.isChecked():
            volume_level = "low"
        elif self.volume_high_rb.isChecked():
            volume_level = "high"

        return {
            'language': self.language_combo.currentData(),
            'update_interval': self.update_interval_spinbox.value(),
            'autostart': self.autostart_checkbox.isChecked(),
            'notifications': self.notifications_checkbox.isChecked(),
            'sound': self.sound_checkbox.isChecked(),
            'volume_level': volume_level,
            'idle_enabled': self.idle_enabled_checkbox.isChecked(),
            'idle_threshold_mins': self.idle_threshold_spinbox.value(),
            'idle_interval_mins': self.idle_interval_spinbox.value(),
        }

class CustomQuestionDialog(QtWidgets.QDialog):
    def __init__(self, title, text, tr, app_icon, parent=None):
        super().__init__(parent)
        self.tr = tr
        self.setWindowTitle(title)
        self.setWindowIcon(app_icon)
        
        self.setObjectName("aboutDialog")
        self.setStyleSheet(themes.get_about_dialog_style())

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(15, 15, 15, 15)

        content_layout = QtWidgets.QHBoxLayout()
        icon_label = QtWidgets.QLabel()
        icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxQuestion)
        icon_label.setPixmap(icon.pixmap(48, 48))
        content_layout.addWidget(icon_label)
        
        text_label = QtWidgets.QLabel(text)
        text_label.setWordWrap(True)
        content_layout.addWidget(text_label, 1)
        layout.addLayout(content_layout)

        button_box = QtWidgets.QDialogButtonBox(self)
        
        yes_button = button_box.addButton(self.tr.get("button_yes"), QtWidgets.QDialogButtonBox.ButtonRole.YesRole)
        no_button = button_box.addButton(self.tr.get("button_no"), QtWidgets.QDialogButtonBox.ButtonRole.NoRole)

        yes_button.setStyleSheet(themes.get_button_style("ok"))
        no_button.setStyleSheet(themes.get_button_style("cancel"))
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(button_box)
        layout.addLayout(button_layout)

    def get_settings(self):
        volume_level = "medium"
        if self.volume_low_rb.isChecked():
            volume_level = "low"
        elif self.volume_high_rb.isChecked():
            volume_level = "high"
        return {
            'language': self.language_combo.currentData(), 'update_interval': self.update_interval_spinbox.value(),
            'autostart': self.autostart_checkbox.isChecked(), 'notifications': self.notifications_checkbox.isChecked(),
            'sound': self.sound_checkbox.isChecked(), 'idle_enabled': self.idle_enabled_checkbox.isChecked(), 'volume_level': volume_level,
            'idle_threshold_mins': self.idle_threshold_spinbox.value(), 'idle_interval_mins': self.idle_interval_spinbox.value(),
        }
