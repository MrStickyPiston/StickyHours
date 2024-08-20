import re
import string
from pprint import pprint

from commonfreehours import utils

languages = ["en", "nl"]

def extract_translations(file_path):
    # Define the regex pattern to match _('')
    pattern = re.compile(r"_\(['\"](.*?)['\"]\)")

    # Read the content of the file
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Find all matches in the content
    matches = pattern.findall(content)

    return matches


class Lang:
    def __init__(self):
        self.lang = utils.get_locale()

        self.languages = {'en': {'auth.button.help': 'Help',
                                 'auth.button.idle': 'Log in',
                                 'auth.button.progress': 'Logging in...',
                                 'auth.message.failed.credentials': 'Invalid account name or password.',
                                 'auth.message.failed.fields': 'Some fields are empty. Please fill in '
                                                               'all fields.',
                                 'auth.message.failed.instance_id': 'Incorrect zermelo instance id.',
                                 'auth.message.failed.title': 'Authentication failed',
                                 'auth.password': 'Zermelo account password',
                                 'auth.school': 'Zermelo portal id',
                                 'auth.user': 'Zermelo account name',
                                 'auth.window.title': 'Zermelo login',
                                 'command.group.account': 'Account',
                                 'command.logout': 'Log out',
                                 'command.logout.confirm.message': 'Are you sure you want to log out?',
                                 'command.logout.confirm.title': 'Confirm logging out',
                                 'command.logout.success.message': 'Successfully logged out.',
                                 'command.logout.success.title': 'Logged out',
                                 'error.auth.message': "Your zermelo session has been expired. Please log in again.",
                                 'error.auth.title': "Session expired",
                                 'error.data.message': "The zermelo api returned incorrect or faulty data. Please report this on the issue tracker.",
                                 'error.data.title': "Error: invalid data",
                                 'error.function_settings.message': "Your school set school function setting {} to {} but it is required to be {} for endpoint {}.",
                                 'error.function_settings.title': "Error: invalid settings",
                                 'error.http_status.message': "The zermelo api returned an error. Please try again.",
                                 'error.http_status.title': "Zermelo api error",
                                 'error.network.message': "You are not connected to the internet or the zermelo servers are down. Please try again",
                                 'error.network.title': "Error: no connection",
                                 'error.other.message': "Something went wrong. Please report the error below to the issue tracker.",
                                 'error.other.title': "Unexpected error",
                                 'main.button.add_entry': 'Add user',
                                 'main.button.idle': 'Compute',
                                 'main.button.listing': 'Listing data...',
                                 'main.button.processing': 'Processing data...',
                                 'main.button.remove_entry': 'Remove user',
                                 'main.label.entries': 'Users',
                                 'main.label.weeks_amount': 'Amount of weeks',
                                 'main.message.failed.error': 'An error occured. Please report the '
                                                              'error below to the issue tracker:',
                                 'main.message.failed.title': 'Computing common free hours failed',
                                 'main.message.no_schedule_user.message': 'User {} has no schedule available.',
                                 'main.message.no_schedule_user.title': "No schedule found for user.",
                                 'main.placeholder.filter_entry': 'Filter users...',
                                 'main.results.header': 'Common free hours',
                                 'main.results.none': 'No common free hours found.'},
                          'nl': {'auth.button.help': 'Hulp met inloggen',
                                 'auth.button.idle': 'Log in',
                                 'auth.button.progress': 'Aan het inloggen...',
                                 'auth.message.failed.credentials': 'Verkeerd wachtwoord of '
                                                                    'gebruikersnaam.',
                                 'auth.message.failed.fields': 'Vul alle velden in',
                                 'auth.message.failed.instance_id': 'Incorrecte zermelo portal id',
                                 'auth.message.failed.title': 'Probleem bij inloggen',
                                 'auth.password': 'Zermelo wachtwoord',
                                 'auth.school': 'Zermelo portal id',
                                 'auth.user': 'Zermelo gebruikersnaam',
                                 'auth.window.title': 'Zermelo login',
                                 'command.group.account': 'Account',
                                 'command.logout': 'Afmelden',
                                 'command.logout.confirm.message': 'Weet je zeker dat je wilt afmelden?',
                                 'command.logout.confirm.title': 'Afmelden bevestigen',
                                 'command.logout.success.message': 'Successvol afgemeld.',
                                 'command.logout.success.title': 'Account afgemeld',
                                 'error.auth.message': 'Uw sessie is verlopen. Log opnieuw in.',
                                 'error.auth.title': 'Sessie verlopen',
                                 'error.data.message': 'De Zermelo api stuurde verkeerde data terug. Rapporteer dit op de issue tracker.',
                                 'error.data.title': 'Fout: verkeerde data',
                                 'error.function_settings.message': "De school heeft de school function setting {} ingesteld als {} maar moet {} zijn zodat api endpoint {} goed werkt.",
                                 'error.function_settings.title': 'Error: verkeerde instelling',
                                 'error.http_status.message': 'De Zermelo api stuurde een fout terug. Probeer het later nog eens.',
                                 'error.http_status.title': 'Zermelo api fout',
                                 'error.network.message': 'Geen verbinding met de servers van zermelo. Controleer de verbinding met het internet en probeer het nog eens.',
                                 'error.network.title': 'Geen verbinding',
                                 'error.other.message': 'Er is iets misgegaan. Rapporteer deze fout op de issuetracker.',
                                 'error.other.title': 'Onverwachte fout',
                                 'main.button.add_entry': 'Gebruiker toevoegen',
                                 'main.button.idle': 'Vind gezamelijke tussenuren',
                                 'main.button.listing': 'Gegevens weergeven...',
                                 'main.button.processing': 'Gegevens verwerken...',
                                 'main.button.remove_entry': 'Gebruiker verwijderen',
                                 'main.label.entries': 'Gebruikers',
                                 'main.label.weeks_amount': 'Aantal weken',
                                 'main.message.failed.error': 'Er is iets fout gegaan. Rapporteer de '
                                                              'onderstaande fout op de issuetracker:',
                                 'main.message.failed.title': 'Probleem tijdens het vinden van '
                                                              'gemeenschappelijke uren',
                                 'main.message.no_schedule_user.message': 'Geen rooster gevonden voor gebruiker {}.',
                                 'main.message.no_schedule_user.title': 'Geen rooster gevonden',
                                 'main.placeholder.filter_entry': 'Gebruikers filteren...',
                                 'main.results.header': 'Gezamelijke tussenuren',
                                 'main.results.none': 'Geen gezamelijke tussenuren.'}}

        print(f'Detected language {self.lang}')

        if not self.languages.get(self.lang):
            print('Defaulting to english')
            self.lang = 'en'

    def translate(self, key: string):

        value: string = self.languages.get(self.lang, self.languages.get('en')).get(key, '')

        if value == '':
            print('Missing key, rerun the script to regenerate keys')

        if value == '' or value is None:
            print(f'Empty key: {self.lang}/{key}')

            if self.lang == 'en':
                return key

            # use the english version if not found normally
            # return the key if value is not found
            value = self.languages.get('en').get(key, key)

            if value == '':
                print(f'Empty key: en/{key}')
                value = key

        return value

if __name__ == "__main__":
    translations = {}

    lang = Lang()

    for l in languages:
        translations[l] = {}
        for key in extract_translations('app.py'):
            translations[l][key] = lang.languages.get(l).get(key)

    pprint({lang: dict(sorted(entries.items())) for lang, entries in translations.items()})
