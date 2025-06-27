# TrayFlag v1.0.0

**A simple and powerful tray indicator for your current IP address location.**

TrayFlag is a lightweight, portable utility for Windows that displays the flag of your current IP address's country right in the system tray. It's an ideal tool for VPN users, developers, and anyone who wants to quickly monitor their network location.

![TrayFlag Screenshot](https://raw.githubusercontent.com/Ridbowt/TrayFlag/main/Promo/screenshot.png) 
*(Note: You will need to upload this screenshot yourself, see instructions below)*

## Features

*   **Real-time Tray Icon:** Instantly see the country flag of your current IP.
*   **Detailed Information:** A clean tooltip shows your IP, country code, city, and provider. The context menu provides full, unabbreviated details.
*   **Interactive History:** View and copy your last 3 IP locations directly from the menu.
*   **Adaptive Updates:** An intelligent timer saves resources by switching between a fast "active" mode and a slower "idle" mode.
*   **Fully Portable:** Leaves no traces in the registry. All settings are stored in a local `TrayFlag.ini` file.
*   **Customizable:** A user-friendly settings dialog to control update intervals, notifications, sound, and autostart behavior.
*   **Multilingual:** Supports multiple languages with auto-detection of your system's language on first launch.

## Installation

1.  Go to the [**Releases**](https://github.com/Ridbowt/TrayFlag/releases) page.
2.  Download the latest `.zip` archive (e.g., `TrayFlag_v1.0.0_win-x64.zip`).
3.  Unzip the archive to any folder on your computer.
4.  Run `TrayFlag.exe`.

## System Requirements

*   **Operating System:** Windows 10 (x64) or Windows 11 (x64).
*   *Note: The application is not compatible with Windows 7/8 or 32-bit systems due to limitations of modern Python versions and required libraries.*

## How to Contribute

Found a bug or have an idea for a new feature? Feel free to open a new issue in the [**Issues**](https://github.com/Ridbowt/TrayFlag/issues) section.

You can also contribute by translating TrayFlag into your language! Simply copy `assets/i18n/en.json`, translate the values, and share the new file.

---
*This application was created by an enthusiast with significant support and consultation from AI assistants (Google AI Studio, ChatGPT).*