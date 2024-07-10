import locale
import string

import toga.platform

if toga.platform.get_current_platform() == 'android':
    import java

    def get_locale():
        Resources = java.jclass('android.content.res.Resources')

        resources = Resources.getSystem()
        configuration = resources.getConfiguration()

        locale_list = configuration.getLocales()
        return locale_list.get(0).toString()

        return java.jclass('java.util.Locale').getDefault()
else:
    locale.setlocale(locale.LC_ALL, '')

    def get_locale():
        return locale.getdefaultlocale()[0]


class Lang:
    def __init__(self):
        self.lang = get_locale()

        self.languages = {
            "en_US": {
                "command.group.account": "Account",
                "command.logout": "Log out",
                "main.settings.header": "Settings",
                "main.accounts.1.title": "Account 1",
                "main.accounts.search": "Search accounts",
                "main.accounts.2.title": "Account 2",
                "main.breaks.header": "Breaks",
                "main.breaks.show": "Also show breaks",
                "main.results.placeholder": "Result will be shown here",
                "auth.header": "Zermelo login",
                "auth.school": "School / organization",
                "auth.user": "Account name",
                "auth.password": "Account password",
                "auth.is_teacher": "Account is a teacher account",
                "auth.button.idle": "Log in",
                "auth.window.title": "Zermelo login",
                "auth.message.failed.message.fields": "Please fill in all fields and try again.",
                "auth.message.failed.title": "Authentication failed",
                "auth.button.progress": "Logging in...",
                "auth.message.failed.message": "Please check if the credentials are right and try again.",
                "command.logout.confirm.message": "Are you sure you want to log out?",
                "command.logout.confirm.title": "Confirm logging out",
                "command.logout.success.message": "Successfully logged out.",
                "command.logout.success.title": "Logged out",
                "main.button.fetching": "Fetching data...",
                "main.button.idle": "Compute",
                "main.button.processing": "Processing data...",
                "main.button.listing": "Listing data...",
                "main.results.header": "Common free hours",
                "common.no": "no",
                "common.yes": "yes",
                "main.results.break.indicator.text": "BREAK",
                "main.results.none": "No common free hours found."
            },

            "nl_NL": {
                "command.group.account": "Account",
                "command.logout": "Afmelden",
                "main.settings.header": "Instellingen",
                "main.accounts.1.title": "Account 1",
                "main.accounts.search": "Kies een account",
                "main.accounts.2.title": "Account 2",
                "main.breaks.header": "Pauzes",
                "main.breaks.show": "Pauzes weergeven",
                "main.results.placeholder": "De resultaten zullen hier komen te staan.",
                "auth.header": "Zermelo login",
                "auth.school": "School / organisatie",
                "auth.user": "Zermelo gebruikersnaam",
                "auth.password": "Zermelo wachtwoord",
                "auth.is_teacher": "Dit account is een lerarenaccount",
                "auth.button.idle": "Log in",
                "auth.window.title": "Zermelo login",
                "auth.message.failed.message.fields": "Vul alles in en probeer het opnieuw.",
                "auth.message.failed.title": "Probleem bij inloggen",
                "auth.button.progress": "Aan het inloggen...",
                "auth.message.failed.message": "Controleer of de gegevens juist zijn en probeer het opnieuw.",
                "command.logout.confirm.message": "Weet je zeker dat je wilt afmelden?",
                "command.logout.confirm.title": "Afmelden bevestigen",
                "command.logout.success.message": "Successvol afgemeld.",
                "command.logout.success.title": "Account afgemeld",
                "main.button.fetching": "Gegevens ophalen... ",
                "main.button.idle": "Vind gezamelijke tussenuren",
                "main.button.processing": "Gegevens verwerken...",
                "main.button.listing": "Gegevens weergeven...",
                "main.results.header": "Gezamelijke tussenuren",
                "common.no": "Nee",
                "common.yes": "Ja",
                "main.results.break.indicator.text": "PAUZE",
                "main.results.none": "Geen gezamelijke tussenuren gevonden."
            }
        }

        print(f'Detected language {self.lang}')

        if not self.languages.get(self.lang):
            print('Defaulting to english')
            self.lang = 'en_US'

    def translate(self, key: string):

        value: string = self.languages.get(self.lang, self.languages.get('en_US')).get(key, '')

        if value == '':
            print(f'Empty key: {self.lang}/{key}')

            if self.lang == 'en_US':
                return key

            # use the english version if not found normally
            # return the key if value is not found
            value = self.languages.get('en_US').get(key, key)

            if value == '':
                print(f'Empty key: en_US/{key}')
                value = key

        return value
