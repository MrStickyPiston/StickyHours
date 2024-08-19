import locale
import string
import webbrowser

from toga.style import Pack

platform = 'OTHER'

locale.setlocale(locale.LC_ALL, '')

button_style = Pack()


def open_url(url: string):
    webbrowser.open(url)


def get_locale():
    return locale.getlocale()[0].split('_')[0]
