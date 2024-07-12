import locale
import string
import webbrowser

locale.setlocale(locale.LC_ALL, '')

def open_url(url: string):
    webbrowser.open(url)

def get_locale():
    return locale.getdefaultlocale()[0]