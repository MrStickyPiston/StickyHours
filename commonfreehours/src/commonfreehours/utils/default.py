import locale
import string
import webbrowser

from toga.style import Pack

locale.setlocale(locale.LC_ALL, '')

button_style = Pack()


def open_url(url: string):
    webbrowser.open(url)


def get_locale():
    return locale.getdefaultlocale()[0].split('-')[0]
