# File: src/utils.py

import sys
import os
import re
import shutil
import subprocess
from PySide6 import QtWidgets, QtGui, QtCore
from constants import APP_NAME

def get_base_path():
    """
    Returns the base path of the application
    """
    #return os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # <--- WHEN RUNNING FROM A .PY SCRIPT
    return os.path.dirname(os.path.abspath(__file__)) # <--- WHEN RUNNING FROM THE .EXE APPLICATION

def resource_path(relative_path):
    return os.path.join(get_base_path(), relative_path)

def clean_isp_name(isp_name):
    if not isp_name: return "N/A"
    isp_name = re.sub(r'\bAS\d+\b|\(\s*AS\d+\s*\)', '', isp_name, flags=re.IGNORECASE).strip()
    words_to_remove = [
        "PJSC", "LLC", "Ltd", "Inc", "Corp", "Corporation", "Company", "Co",
        "Public Joint Stock Company", "Limited Liability Company",
        "Joint Stock Company", "Open Joint Stock Company",
        "Private Limited Company", "PLC", "GmbH", "AG", "SA", "S.A.", "S.P.A.", "S.R.L.",
        "Internet Service Provider", "ISP", "Telecommunications", "Communications",
        "Network", "Solutions", "Technologies", "Services", "Group", "Holding",
        "LLP", "LP", "PC", "SC", "O.O.O.", "ZAO", "OAO", "PAO", "JSC", "CJSC"
    ]
    pattern = r'\b(?:' + '|'.join(re.escape(word) for word in words_to_remove) + r')\b\.?\s*'
    isp_name = re.sub(pattern, '', isp_name, flags=re.IGNORECASE).strip()
    isp_name = isp_name.replace("  ", " ").strip(' -.,')
    return isp_name if isp_name else "N/A"

def truncate_text(text, max_length):
    return text[:max_length-3] + "..." if len(text) > max_length else text

def get_country_name(country_code):
    """
    Returns full country name for a given 2-letter country code.
    Falls back to the code itself if not found.
    Includes all 271 territories from flag-icons package.
    """
    if not country_code or len(country_code) != 2:
        return "N/A"
    
    # Complete dictionary of country codes → full names
    country_names = {
        "AD": "Andorra", "AE": "United Arab Emirates", "AF": "Afghanistan",
        "AG": "Antigua and Barbuda", "AI": "Anguilla", "AL": "Albania",
        "AM": "Armenia", "AO": "Angola", "AQ": "Antarctica", "AR": "Argentina",
        "AS": "American Samoa", "AT": "Austria", "AU": "Australia",
        "AW": "Aruba", "AX": "Åland Islands", "AZ": "Azerbaijan",
        "BA": "Bosnia and Herzegovina", "BB": "Barbados", "BD": "Bangladesh",
        "BE": "Belgium", "BF": "Burkina Faso", "BG": "Bulgaria",
        "BH": "Bahrain", "BI": "Burundi", "BJ": "Benin", "BL": "Saint Barthélemy",
        "BM": "Bermuda", "BN": "Brunei", "BO": "Bolivia", "BQ": "Caribbean Netherlands",
        "BR": "Brazil", "BS": "Bahamas", "BT": "Bhutan", "BV": "Bouvet Island",
        "BW": "Botswana", "BY": "Belarus", "BZ": "Belize", "CA": "Canada",
        "CC": "Cocos Islands", "CD": "DR Congo", "CF": "Central African Republic",
        "CG": "Republic of the Congo", "CH": "Switzerland", "CI": "Côte d'Ivoire",
        "CK": "Cook Islands", "CL": "Chile", "CM": "Cameroon", "CN": "China",
        "CO": "Colombia", "CP": "Clipperton Island", "CR": "Costa Rica",
        "CU": "Cuba", "CV": "Cape Verde", "CW": "Curaçao", "CX": "Christmas Island",
        "CY": "Cyprus", "CZ": "Czechia", "DE": "Germany", "DG": "Diego Garcia",
        "DJ": "Djibouti", "DK": "Denmark", "DM": "Dominica", "DO": "Dominican Republic",
        "DZ": "Algeria", "EA": "Ceuta & Melilla", "EC": "Ecuador", "EE": "Estonia",
        "EG": "Egypt", "EH": "Western Sahara", "ER": "Eritrea", "ES": "Spain",
        "ET": "Ethiopia", "EU": "European Union", "FI": "Finland", "FJ": "Fiji",
        "FK": "Falkland Islands", "FM": "Micronesia", "FO": "Faroe Islands",
        "FR": "France", "GA": "Gabon", "GB": "United Kingdom", "GD": "Grenada",
        "GE": "Georgia", "GF": "French Guiana", "GG": "Guernsey", "GH": "Ghana",
        "GI": "Gibraltar", "GL": "Greenland", "GM": "Gambia", "GN": "Guinea",
        "GP": "Guadeloupe", "GQ": "Equatorial Guinea", "GR": "Greece",
        "GS": "South Georgia", "GT": "Guatemala", "GU": "Guam", "GW": "Guinea-Bissau",
        "GY": "Guyana", "HK": "Hong Kong", "HM": "Heard & McDonald Islands",
        "HN": "Honduras", "HR": "Croatia", "HT": "Haiti", "HU": "Hungary",
        "IC": "Canary Islands", "ID": "Indonesia", "IE": "Ireland", "IL": "Israel",
        "IM": "Isle of Man", "IN": "India", "IO": "British Indian Ocean Territory",
        "IQ": "Iraq", "IR": "Iran", "IS": "Iceland", "IT": "Italy", "JE": "Jersey",
        "JM": "Jamaica", "JO": "Jordan", "JP": "Japan", "KE": "Kenya",
        "KG": "Kyrgyzstan", "KH": "Cambodia", "KI": "Kiribati", "KM": "Comoros",
        "KN": "Saint Kitts and Nevis", "KP": "North Korea", "KR": "South Korea",
        "KW": "Kuwait", "KY": "Cayman Islands", "KZ": "Kazakhstan", "LA": "Laos",
        "LB": "Lebanon", "LC": "Saint Lucia", "LI": "Liechtenstein", "LK": "Sri Lanka",
        "LR": "Liberia", "LS": "Lesotho", "LT": "Lithuania", "LU": "Luxembourg",
        "LV": "Latvia", "LY": "Libya", "MA": "Morocco", "MC": "Monaco",
        "MD": "Moldova", "ME": "Montenegro", "MF": "Saint Martin", "MG": "Madagascar",
        "MH": "Marshall Islands", "MK": "North Macedonia", "ML": "Mali", "MM": "Myanmar",
        "MN": "Mongolia", "MO": "Macao", "MP": "Northern Mariana Islands",
        "MQ": "Martinique", "MR": "Mauritania", "MS": "Montserrat", "MT": "Malta",
        "MU": "Mauritius", "MV": "Maldives", "MW": "Malawi", "MX": "Mexico",
        "MY": "Malaysia", "MZ": "Mozambique", "NA": "Namibia", "NC": "New Caledonia",
        "NE": "Niger", "NF": "Norfolk Island", "NG": "Nigeria", "NI": "Nicaragua",
        "NL": "Netherlands", "NO": "Norway", "NP": "Nepal", "NR": "Nauru",
        "NU": "Niue", "NZ": "New Zealand", "OM": "Oman", "PA": "Panama",
        "PC": "Pacific Islands Trust Territory", "PE": "Peru", "PF": "French Polynesia",
        "PG": "Papua New Guinea", "PH": "Philippines", "PK": "Pakistan",
        "PL": "Poland", "PM": "Saint Pierre and Miquelon", "PN": "Pitcairn Islands",
        "PR": "Puerto Rico", "PS": "Palestine", "PT": "Portugal", "PW": "Palau",
        "PY": "Paraguay", "QA": "Qatar", "RE": "Réunion", "RO": "Romania",
        "RS": "Serbia", "RU": "Russia", "RW": "Rwanda", "SA": "Saudi Arabia",
        "SB": "Solomon Islands", "SC": "Seychelles", "SD": "Sudan", "SE": "Sweden",
        "SG": "Singapore", "SH": "Saint Helena", "SI": "Slovenia", "SJ": "Svalbard and Jan Mayen",
        "SK": "Slovakia", "SL": "Sierra Leone", "SM": "San Marino", "SN": "Senegal",
        "SO": "Somalia", "SR": "Suriname", "SS": "South Sudan", "ST": "São Tomé and Príncipe",
        "SV": "El Salvador", "SX": "Sint Maarten", "SY": "Syria", "SZ": "Eswatini",
        "TC": "Turks and Caicos Islands", "TD": "Chad", "TF": "French Southern Territories",
        "TG": "Togo", "TH": "Thailand", "TJ": "Tajikistan", "TK": "Tokelau",
        "TL": "Timor-Leste", "TM": "Turkmenistan", "TN": "Tunisia", "TO": "Tonga",
        "TR": "Turkey", "TT": "Trinidad and Tobago", "TV": "Tuvalu", "TW": "Taiwan",
        "TZ": "Tanzania", "UA": "Ukraine", "UG": "Uganda", "UM": "U.S. Outlying Islands",
        "UN": "United Nations", "US": "United States", "UY": "Uruguay", "UZ": "Uzbekistan",
        "VA": "Vatican City", "VC": "Saint Vincent and the Grenadines", "VE": "Venezuela",
        "VG": "British Virgin Islands", "VI": "U.S. Virgin Islands", "VN": "Vietnam",
        "VU": "Vanuatu", "WF": "Wallis and Futuna", "WS": "Samoa", "XK": "Kosovo",
        "XX": "Unknown", "YE": "Yemen", "YT": "Mayotte", "ZA": "South Africa",
        "ZM": "Zambia", "ZW": "Zimbabwe",
    }
    
    code_upper = country_code.strip().upper()
    return country_names.get(code_upper, code_upper)  # Fallback: вернёт код, если не найдено
    
    code_upper = country_code.strip().upper()
    return country_names.get(code_upper, code_upper)  # Fallback: вернёт код, если не найдено

def set_autostart_shortcut(enabled):
    if sys.platform != 'win32': return
    try:
        import win32com.client
    except ImportError:
        print("WARNING: pywin32 library not found. Autostart feature is disabled.")
        return
        
    shell = win32com.client.Dispatch("WScript.Shell")
    startup_folder = shell.SpecialFolders("Startup")
    shortcut_path = os.path.join(startup_folder, f"{APP_NAME}.lnk")
    
    if enabled:
        main_exe_path = resource_path(f"{APP_NAME}.exe")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = main_exe_path
        shortcut.IconLocation = resource_path(os.path.join("assets", "icons", "logo.ico"))
        shortcut.Description = f"Start {APP_NAME}"
        shortcut.WorkingDirectory = get_base_path()
        shortcut.save()
        print(f"Autostart shortcut created at: {shortcut_path}")
    else:
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            print(f"Autostart shortcut removed from: {shortcut_path}")

def create_no_internet_icon(size=20):
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    pen = QtGui.QPen(QtCore.Qt.GlobalColor.red)
    pen.setWidth(3)
    painter.setPen(pen)
    painter.drawLine(3, 3, size - 4, size - 4)
    painter.drawLine(size - 4, 3, 3, size - 4)
    painter.end()
    return QtGui.QIcon(pixmap)

def is_warp_indicator_needed(isp, asn=""):
    """
    Returns True if ISP/ASN indicates Cloudflare WARP usage.
    Conditions: ISP contains 'Cloudflare' or 'WARP', or ASN = AS209242
    """
    isp_lower = isp.lower() if isp else ""
    
    # Check ISP name
    if "cloudflare" in isp_lower or "warp" in isp_lower:
        return True
    
    # Check ASN
    if asn and asn.upper() == "AS209242":
        return True
    
    return False

def create_desktop_shortcut():
    """
    Creates a desktop shortcut for the application if it doesn't exist
    """
    # This function is only for Windows
    if sys.platform != 'win32':
        return

    try:
        import win32com.client
    except ImportError:
        print("WARNING: pywin32 library not found. Desktop shortcut feature is disabled.")
        return
        
    shell = win32com.client.Dispatch("WScript.Shell")
    
    # Get the path to the user's desktop
    desktop_folder = shell.SpecialFolders("Desktop")
    shortcut_path = os.path.join(desktop_folder, f"{APP_NAME}.lnk")
    
    # Check if the shortcut already exists
    if os.path.exists(shortcut_path):
        print(f"Desktop shortcut already exists at: {shortcut_path}")
        return

    # Get the path to our compiled .exe
    main_exe_path = resource_path(f"{APP_NAME}.exe")
    
    # Create a shortcut object and configure its properties
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = main_exe_path
    shortcut.IconLocation = resource_path(os.path.join("assets", "icons", "logo.ico"))
    shortcut.Description = f"Launch {APP_NAME}"
    shortcut.WorkingDirectory = get_base_path()
    
    # Save the shortcut
    shortcut.save()
    print(f"Desktop shortcut created at: {shortcut_path}")

def run_updater_script():
    """
    Finds and runs the updater.ps1 script, giving preference to PowerShell 7.
    """
    updater_path = resource_path("updater.ps1")
    if not os.path.exists(updater_path):
        print(f"[ERROR] updater.ps1 not found at: {updater_path}")
        # You can show a QMessageBox with an error here if needed
        return

    # Ищем pwsh.exe (PowerShell 7+)
    pwsh_path = shutil.which("pwsh")
    
    if pwsh_path:
        command = [pwsh_path, "-ExecutionPolicy", "Bypass", "-File", updater_path]
    else:
        command = ["powershell", "-ExecutionPolicy", "Bypass", "-File", updater_path]
    
    # Run in a new console
    subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
