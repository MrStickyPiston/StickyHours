import ctypes
import locale

platform = "WINDOWS"

icon_button_size = 24

def get_locale():
    windll = ctypes.windll.kernel32
    return locale.windows_locale[windll.GetUserDefaultUILanguage()].split('_')[0]