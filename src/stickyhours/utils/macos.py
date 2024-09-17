from .default import get_locale as unsafe_get_locale

platform = "MACOS"
icon_button_size = 24

def get_locale():
    try:
        return unsafe_get_locale()
    except AttributeError:
        return None