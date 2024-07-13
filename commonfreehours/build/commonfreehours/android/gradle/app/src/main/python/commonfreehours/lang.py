import string

from commonfreehours import utils


class Lang:
    def __init__(self):
        self.lang = utils.get_locale()

        self.languages = {
            "en_US": {
                "command.group.account": "Account",
                "command.logout": "Log out",
                "main.accounts.1.title": "Account 1",
                "main.accounts.search": "Search accounts",
                "main.accounts.2.title": "Account 2",
                "main.breaks.header": "Breaks",
                "main.breaks.show": "Also show breaks",
                "main.results.placeholder": "Result will be shown here",
                "auth.school": "Zermelo portal id",
                "auth.user": "Zermelo account name",
                "auth.password": "Zermelo account password",
                "auth.is_teacher": "Account is a teacher account",
                "auth.button.idle": "Log in",
                "auth.window.title": "Zermelo login",
                "auth.message.failed.message.fields": "Please fill in all fields and try again.",
                "auth.message.failed.title": "Authentication failed",
                "auth.button.progress": "Logging in...",
                "auth.message.failed.message": "Please check if the credentials are right and try again, or click the "
                                               "help button for more information.",
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
                "main.results.none": "No common free hours found.",
                "main.error.no-schedule.title": "No schedule found",
                "main.error.no-schedule.message": "No schedule with gaps found for {}.",
                "auth.error.expired.title": "Session expired",
                "auth.error.expired.message": "Please log in again to renew the session.",
                "auth.button.help": "Help"
            },

            "nl_NL": {
                "command.group.account": "Account",
                "command.logout": "Afmelden",
                "main.accounts.1.title": "Account 1",
                "main.accounts.search": "Kies een account",
                "main.accounts.2.title": "Account 2",
                "main.breaks.header": "Pauzes",
                "main.breaks.show": "Pauzes weergeven",
                "main.results.placeholder": "De resultaten zullen hier komen te staan.",
                "auth.school": "Zermelo portal id",
                "auth.user": "Zermelo gebruikersnaam",
                "auth.password": "Zermelo wachtwoord",
                "auth.is_teacher": "Dit account is een lerarenaccount",
                "auth.button.idle": "Log in",
                "auth.window.title": "Zermelo login",
                "auth.message.failed.message.fields": "Vul alles in en probeer het opnieuw.",
                "auth.message.failed.title": "Probleem bij inloggen",
                "auth.button.progress": "Aan het inloggen...",
                "auth.message.failed.message": "Controleer of de gegevens juist zijn en probeer het opnieuw, of klik op de hulpknop voor meer informatie.",
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
                "main.results.none": "Geen gezamelijke tussenuren.",
                "main.error.no-schedule.title": "Geen rooster gevonden",
                "main.error.no-schedule.message": "Geen rooster gevonden voor {}.",
                "auth.error.expired.title": "Sessie verlopen",
                "auth.error.expired.message": "Log opnieuw in om de sessie te vernieuwen.",
                "auth.button.help": "Hulp met inloggen"
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
