"""
Easily check for common free hours in zermelo.
"""
import binascii
import datetime
import pathlib
from enum import Enum

import toga
import configparser

import urllib3.exceptions

from commonfreehours import zapi
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from commonfreehours.commonFreeHours import free_common_hours


class FontSize(Enum):
    small = 14
    large = 16
    big = 22


class CommonFreeHours(toga.App):
    def __init__(self):
        super().__init__()

    def startup(self):
        # Main window of the application
        self.main_window = toga.MainWindow(title=self.formal_name)

        self.config = configparser.ConfigParser()
        self.config.read(self.paths.data / 'commonFreeHours.ini')
        self.config['DEFAULT'] = {
            'user1': '',
            'user1teacher': False,
            'user2': '',
            'user2teacher': False
        }

        if 'user' not in self.config.sections():
            self.config['user'] = {}

        self.user_config = self.config['user']

        self.login_setup()
        self.main_setup()

        if self.user_config.get('school') is None or self.user_config.get('account_name') is None:
            self.login_setup()
            self.login_view()
        else:
            try:
                self.zermelo = zapi.zermelo(
                    self.user_config.get('school'),
                    self.user_config.get('account_name'),
                    teacher=self.user_config.get('teacher'),
                    version=3,
                    token_file=self.paths.data / 'ZToken'
                )

                try:
                    self.zermelo.get_raw_schedule()
                    print(
                        f"Used existing zermelo instance as {self.user_config.get('account_name')} on {self.user_config.get('school')} with teacher={self.user_config.get('teacher')}")
                    self.main()
                except ValueError:
                    # If zermelo auth expired
                    pathlib.Path(self.paths.data / 'ZToken').unlink(missing_ok=True)
                    pathlib.Path(self.paths.data / 'commonFreeHours.ini').unlink(missing_ok=True)
                    self.login_view()
            except (
                    binascii.Error,  #
                    ValueError,  # For incorrect config file no token
                    urllib3.exceptions.LocationParseError  # Catch zermelo 404
            ):
                pathlib.Path(self.paths.data / 'ZToken').unlink(missing_ok=True)
                pathlib.Path(self.paths.data / 'commonFreeHours.ini').unlink(missing_ok=True)
                self.login_setup()
                self.login_view()
            # Set the main window's content

        self.main_window.show()

    def main_setup(self):

        # Main box to hold all widgets
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.main_container = toga.ScrollContainer(content=main_box, horizontal=False)

        # Compare section
        compare_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))
        compare_box.add(toga.Label('Settings', style=Pack(padding=(0, 5, 10, 5), font_size=FontSize.big.value)))

        # Account name 1
        account1_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 0, 10, 0)))

        self.name1_input = toga.TextInput(style=Pack(flex=1, padding=(0, 5)))
        name1_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))
        name1_box.add(toga.Label('Account 1', style=Pack(padding=(0, 5), font_size=FontSize.large.value)))
        name1_box.add(self.name1_input)
        account1_box.add(name1_box)

        self.is_teacher1 = toga.Switch('', style=Pack(padding=(0, 5), font_size=FontSize.large.value))
        is_teacher1_box = toga.Box(style=Pack(direction=ROW, padding=(0, 5)))
        is_teacher1_box.add(
            toga.Label('Account 1 is a teacher account:', style=Pack(padding=(0, 5), font_size=FontSize.small.value)))
        is_teacher1_box.add(self.is_teacher1)
        account1_box.add(is_teacher1_box)

        compare_box.add(account1_box)

        # Account name 2
        account2_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 0, 10, 0)))

        self.name2_input = toga.TextInput(style=Pack(flex=1, padding=(0, 5)))
        name2_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))
        name2_box.add(toga.Label('Account 2', style=Pack(padding=(0, 5), font_size=FontSize.large.value)))
        name2_box.add(self.name2_input)
        account2_box.add(name2_box)

        self.is_teacher2 = toga.Switch('', style=Pack(padding=(0, 5), font_size=FontSize.large.value))
        is_teacher2_box = toga.Box(style=Pack(direction=ROW, padding=(0, 5)))
        is_teacher2_box.add(
            toga.Label('Account 2 is a teacher account:', style=Pack(padding=(0, 5), font_size=FontSize.small.value)))
        is_teacher2_box.add(self.is_teacher2)
        account2_box.add(is_teacher2_box)

        compare_box.add(account2_box)

        # Breaks
        breaks_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 0, 10, 0)))

        breaks_box.add(toga.Label('Breaks', style=Pack(padding=(0, 5), font_size=FontSize.large.value)))

        self.show_breaks = toga.Switch('', style=Pack(padding=(0, 5), font_size=FontSize.large.value))
        show_breaks_box = toga.Box(style=Pack(direction=ROW, padding=(0, 5)))
        show_breaks_box.add(toga.Label('Also show breaks:', style=Pack(padding=(0, 5), font_size=FontSize.small.value)))
        show_breaks_box.add(self.show_breaks)
        breaks_box.add(show_breaks_box)

        compare_box.add(breaks_box)

        # Compute button
        self.compute_button = toga.Button('Compute', on_press=self.compute, style=Pack(padding=(0, 5)))

        # Result
        self.result_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))

        result_label = toga.Label('Result will be shown here', style=Pack(padding=(0, 5), flex=1))
        self.result_box.add(result_label)

        # Add Compare section to main box
        main_box.add(compare_box)
        main_box.add(self.compute_button)
        main_box.add(self.result_box)

    def main(self):
        self.main_window.title = "CommonFreeHours"

        schoolInSchoolYear = self.zermelo.getSchoolInSchoolYear(self.zermelo.getSchoolInSchoolYears())
        self.zermelo.getAccounts(schoolInSchoolYear)

        self.main_window.content = self.main_container

    def login_setup(self):
        self.login_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # Zermelo credentials section
        zermelo_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))
        zermelo_box.add(
            toga.Label('Zermelo Credentials', style=Pack(padding=(0, 5, 10, 5), font_size=FontSize.big.value)))

        # Zermelo school
        self.zermelo_school = toga.TextInput(style=Pack(flex=1, padding=(0, 5)))
        zermelo_school_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))
        zermelo_school_box.add(
            toga.Label('Zermelo school: (organization):', style=Pack(padding=(0, 5), font_size=FontSize.small.value)))
        zermelo_school_box.add(self.zermelo_school)
        zermelo_box.add(zermelo_school_box)

        # Zermelo user
        self.zermelo_user = toga.TextInput(style=Pack(flex=1, padding=(0, 5)))
        zermelo_user_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))
        zermelo_user_box.add(
            toga.Label('Zermelo account name:', style=Pack(padding=(0, 5), font_size=FontSize.small.value)))
        zermelo_user_box.add(self.zermelo_user)
        zermelo_box.add(zermelo_user_box)

        # Zermelo password
        self.zermelo_password = toga.PasswordInput(style=Pack(flex=1, padding=(0, 5)))
        zermelo_password_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))
        zermelo_password_box.add(
            toga.Label('Zermelo account password:', style=Pack(padding=(0, 5), font_size=FontSize.small.value)))
        zermelo_password_box.add(self.zermelo_password)
        zermelo_box.add(zermelo_password_box)

        self.zermelo_teacher = toga.Switch('', style=Pack(padding=(0, 5), font_size=FontSize.large.value))
        is_teacherz_box = toga.Box(style=Pack(direction=ROW, padding=(0, 5)))
        is_teacherz_box.add(
            toga.Label('Account is a teacher account:', style=Pack(padding=(0, 5), font_size=FontSize.small.value)))
        is_teacherz_box.add(self.zermelo_teacher)
        zermelo_box.add(is_teacherz_box)

        self.login_button = toga.Button('Login', on_press=self.login, style=Pack(padding=(0, 5)))

        # Add Zermelo section to main box
        self.login_box.add(zermelo_box)

        self.login_box.add(self.login_button)

    def login_view(self):
        self.main_window.title = "Login - CommonFreeHours"

        self.zermelo_school.value = self.user_config.get('school')
        self.zermelo_user.value = self.user_config.get('account_name')
        self.zermelo_teacher.value = self.user_config.get('teacher')

        self.main_window.content = self.login_box

    async def login(self, widget):
        if self.zermelo_school.value == '' or self.zermelo_user.value == '' or self.zermelo_password.value == '':
            await self.main_window.error_dialog('Authentication failed', 'Please fill in all fields and try again.')
            return

        print(f"Logging in as {self.zermelo_user.value} on {self.zermelo_school.value} with teacher={self.zermelo_teacher.value}")

        try:
            zermelo = zapi.zermelo(
                school=self.zermelo_school.value,
                username=self.zermelo_user.value,
                teacher=self.zermelo_teacher.value,
                password=self.zermelo_password.value,
                version=3,
                token_file=self.paths.data / 'ZToken',
            )

            self.user_config['school'] = self.zermelo_school.value
            self.user_config['account_name'] = self.zermelo_user.value
            self.user_config['teacher'] = str(self.zermelo_teacher.value)

            print("Logged in successfully")

            with open(self.paths.data / 'commonFreeHours.ini', 'w') as f:
                self.config.write(f)

            print("Saved config")

            self.zermelo = zapi.zermelo(
                self.user_config.get('school'),
                self.user_config.get('account_name'),
                teacher=self.user_config.get('is_teacher'),
                version=3,
                token_file=self.paths.data / 'ZToken'
            )

            print(f"Created new zermelo instance as {self.zermelo_user.value} on {self.zermelo_school.value} with teacher={self.zermelo_teacher.value}")

            self.main()
        except ValueError:
            await self.main_window.error_dialog('Authentication failed', 'Please try again.')

    async def compute(self, widget):

        def is_day_later(date1, date2):
            # Extract dates without time
            date1_date_only = date1.date()
            date2_date_only = date2.date()

            # Calculate the difference between the dates
            date_diff = date2_date_only - date1_date_only

            # Check if the difference is exactly one day
            return date_diff >= datetime.timedelta(days=1)

        name1 = self.name1_input.value
        is_teacher1 = self.is_teacher1.value

        name2 = self.name2_input.value
        is_teacher2 = self.is_teacher2.value

        show_breaks = self.show_breaks.value

        try:
            schedule = self.zermelo.sort_schedule(username=name1, teacher=is_teacher1)
            other_schedule = self.zermelo.sort_schedule(username=name2, teacher=is_teacher2)

        except ValueError:
            # If zermelo auth expired
            pathlib.Path(self.paths.data / 'ZToken').unlink(missing_ok=True)
            pathlib.Path(self.paths.data / 'commonFreeHours.ini').unlink(missing_ok=True)
            await self.main_window.info_dialog('Session expired', 'Please log in again.')
            self.login_view()
            return

        if not schedule:
            await self.main_window.error_dialog('No schedule found', 'No schedule found for user 1.')
            return
        if not other_schedule:
            await self.main_window.error_dialog('No schedule found', 'No schedule found for user 2.')
            return

        hours = free_common_hours(schedule, other_schedule, show_breaks)

        self.result_box.clear()

        self.result_box.add(toga.Label(f"Common free hours:", style=Pack(padding=(0, 5), font_size=FontSize.big.value)))
        self.result_box.add(
            toga.Label(f"Account 1: {name1}\nAccount 2: {name2}\nBreaks shown: {'yes' if show_breaks else 'no'}",
                       style=Pack(padding=(0, 5), font_size=FontSize.small.value)))

        day = datetime.datetime.fromtimestamp(datetime.MINYEAR)

        for hour in hours:
            if is_day_later(day, hour.get('start')):
                day = hour.get('start')
                self.result_box.add(toga.Label(hour.get('start').strftime('\n%A %d %B %Y'),
                                               style=Pack(padding=(0, 5), font_size=FontSize.large.value)))

            if not hour.get('break'):
                self.result_box.add(toga.Label(
                    f"{hour.get('start').strftime('%H:%M')} - {hour.get('end').strftime('%H:%M')} ({hour.get('end') - hour.get('start')})",
                    style=Pack(padding=(0, 5), font_size=FontSize.small.value)))
            elif show_breaks:
                self.result_box.add(toga.Label(
                    f"[BREAK] {hour.get('start').strftime('%H:%M')} - {hour.get('end').strftime('%H:%M')} ({hour.get('end') - hour.get('start')})",
                    style=Pack(padding=(0, 5), font_size=FontSize.small.value)))


def main():
    return CommonFreeHours()
