import locale
import logging
import string
import webbrowser

from toga.style import Pack

platform = 'OTHER'

locale.setlocale(locale.LC_ALL, '')

button_style = Pack()

icon_button_size = 32


def open_url(url: string):
    webbrowser.open(url)


def get_locale():
    try:
        return locale.getlocale()[0].split('_')[0]
    except locale.Error as e:
        logging.error("Failed to get locale: ", e)
