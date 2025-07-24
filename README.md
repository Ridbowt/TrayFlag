TrayFlag v1.5.0

English | Русский

A simple and powerful tray indicator for your current IP address location.

TrayFlag is a lightweight, portable utility for Windows that displays the flag of your current IP address's country right in the system tray. It's an ideal tool for VPN users, developers, and anyone who wants to quickly monitor their network location.

Features
Real-time Tray Icon: Instantly see the country flag of your current IP.

Intelligent IP Monitoring: The application efficiently monitors your external IP address, requesting full geolocation data (country, city, ISP) only when necessary. This approach significantly reduces the number of requests to geolocation services, making the app more efficient and reliable.

Resilient Operation: If geolocation services are temporarily unavailable or your internet connection is lost, the application will actively attempt to restore connection and provide essential information. An audible alert can notify you of network issues.

Detailed Information: A clean tooltip shows your IP, country code, city, and provider. The context menu provides full, unabbreviated details.

Interactive History: View and copy your last 3 IP locations directly from the menu.

Consistent Updates: The application now consistently checks your IP at a single, user-defined "Update Interval" (e.g., every 7 seconds with a small random variation), ensuring continuous monitoring.

Fully Portable: Leaves no traces in the registry. All settings are stored in a local TrayFlag.ini file. The TrayFlag.ini file's version is automatically updated upon launch if it differs from the application's version.

Customizable: A user-friendly settings dialog to control the "Update Interval", notifications, sound, and autostart behavior.

Multilingual: Supports multiple languages with auto-detection of your system's language on first launch.

Installation
Go to the Releases page.

Download the latest .zip archive (e.g., TrayFlag-v1.5.0-windows-x64.zip).

Unzip the archive. This will create a TrayFlag folder.

Open the TrayFlag folder and run TrayFlag.exe.

Important Note: You will see many files (.dll, .pyd) alongside TrayFlag.exe. Among them is also ip_lookup.exe. These are all necessary parts of the application. TrayFlag.exe is the main Python program, and ip_lookup.exe is a helper module written in Go that handles IP address retrieval. It is compiled to run silently without showing a console window. Please do not move or delete them. This file structure is intentionally used to minimize false positive detections by antivirus software.

System Requirements
Operating System: Windows 10 (x64) or Windows 11 (x64).

Note: The application is not compatible with Windows 7/8 or 32-bit systems due to limitations of modern Python versions and required libraries.

How to Contribute
Found a bug or have an idea for a new feature? Feel free to open a new issue in the Issues section.

You can also contribute by translating TrayFlag into your language! The translation files are located in TrayFlag/assets/i18n/. Simply copy en.json, translate the values, and share the new file.

This application was created by an enthusiast with significant support and consultation from AI assistants (Google AI Studio, ChatGPT).