"""
Easily check for common free hours in zermelo.
"""
import asyncio
import binascii
import datetime
import pathlib
from enum import Enum

import requests
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
        self.main_loaded = False
        self.accounts = []

    def startup(self):
        # Main window of the application
        self.main_window = toga.MainWindow(title=self.formal_name)

        # Setup command for logout
        self.account_group = toga.command.Group(
            text='Account',
        )

        self.logout_command = toga.Command(
            self.logout_trigger,
            text='Log out',
            enabled=False,
            group=self.account_group
        )

        self.commands.add(self.logout_command)

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

        if self.user_config.get('school') is None or self.user_config.get('account_name') is None:
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
                    self.schoolInSchoolYear = self.zermelo.getSchoolInSchoolYear(self.zermelo.getSchoolInSchoolYears())
                    self.accounts = self.zermelo.getAccounts(self.schoolInSchoolYear)

                    self.main_setup()
                    self.main_loaded = True

                    print(
                        f"Used existing zermelo instance as {self.user_config.get('account_name')} on {self.user_config.get('school')} with teacher={self.user_config.get('teacher')}")
                    self.main()
                except ValueError:
                    # If zermelo auth expired
                    self.logout_zermelo()
            except (
                    binascii.Error,  #
                    ValueError,  # For incorrect config file no token
                    urllib3.exceptions.LocationParseError,  # Catch zermelo 404
                    requests.exceptions.ConnectionError  # Invalid url
            ):
                self.logout_zermelo()
            # Set the main window's content

        self.main_window.show()

    async def on_change_query_1(self, widget: toga.TextInput):
        options = [option for option in self.accounts if widget.value.lower() in option.get('name').lower()]
        self.name1_selection.items = options

    async def on_change_query_2(self, widget: toga.TextInput):
        options = [option for option in self.accounts if widget.value.lower() in option.get('name').lower()]
        self.name2_selection.items = options

    def main_setup(self):

        # Main box to hold all widgets
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.main_container = toga.ScrollContainer(content=main_box, horizontal=False)

        # Compare section
        compare_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))
        compare_box.add(toga.Label('Settings', style=Pack(padding=(0, 5, 10, 5), font_size=FontSize.big.value)))

        # Account name 1
        account1_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 0, 10, 0)))

        name1_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))

        name1_box.add(toga.Label('Account 1', style=Pack(padding=(0, 5), font_size=FontSize.large.value)))

        self.name1_input = toga.TextInput(
            style=Pack(flex=1, padding=(0, 5)),
            on_change=self.on_change_query_1
        )

        name1_box.add(toga.Label('Search accounts', style=Pack(padding=(0, 5), font_size=FontSize.small.value)))

        name1_box.add(self.name1_input)

        self.name1_selection = toga.Selection(items=self.accounts,
                                              accessor='name',
                                              style=Pack(flex=1, padding=(0, 5)))
        name1_box.add(self.name1_selection)
        account1_box.add(name1_box)

        compare_box.add(account1_box)

        # Account name 2
        account2_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 0, 10, 0)))

        name2_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))

        name2_box.add(toga.Label('Account 2', style=Pack(padding=(0, 5), font_size=FontSize.large.value)))

        self.name2_input = toga.TextInput(
            style=Pack(flex=1, padding=(0, 5)),
            on_change=self.on_change_query_2
        )

        name2_box.add(toga.Label('Search accounts', style=Pack(padding=(0, 5), font_size=FontSize.small.value)))

        name2_box.add(self.name2_input)

        self.name2_selection = toga.Selection(items=self.accounts,
                                              accessor='name',
                                              style=Pack(flex=1, padding=(0, 5)))
        name2_box.add(self.name2_selection)
        account2_box.add(name2_box)

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
        self.compute_button = toga.Button('Compute', on_press=self.compute_scheduler, style=Pack(padding=(0, 5)))

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

        self.logout_command.enabled = True

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

        self.login_button = toga.Button('Login', on_press=self.login_scheduler, style=Pack(padding=(0, 5)))

        # Add Zermelo section to main box
        self.login_box.add(zermelo_box)

        self.login_box.add(self.login_button)

    def login_view(self):
        self.main_window.title = "Login - CommonFreeHours"

        self.logout_command.enabled = False

        self.zermelo_school.value = self.user_config.get('school')
        self.zermelo_user.value = self.user_config.get('account_name')
        self.zermelo_teacher.value = self.user_config.get('teacher')

        self.main_window.content = self.login_box

    def login_scheduler(self, widget):
        asyncio.create_task(self.login())

    async def login(self):
        def login_test():
            zapi.zermelo(
                school=self.zermelo_school.value.strip(),
                username=self.zermelo_user.value.strip(),
                teacher=self.zermelo_teacher.value,
                password=self.zermelo_password.value,
                version=3,
                token_file=self.paths.data / 'ZToken',
            )

        await asyncio.sleep(0)  # Yield to event loop briefly
        loop = asyncio.get_event_loop()

        if self.zermelo_school.value == '' or self.zermelo_user.value == '' or self.zermelo_password.value == '':
            await self.main_window.error_dialog('Authentication failed', 'Please fill in all fields and try again.')
            return

        self.login_button.enabled = False
        self.login_button.text = "Logging in..."

        print(
            f"Logging in as {self.zermelo_user.value} on {self.zermelo_school.value} with teacher={self.zermelo_teacher.value}")

        try:
            await loop.run_in_executor(None, login_test)
        except (RuntimeError, ValueError) as e:
            print(e)
            self.login_button.enabled = True
            self.login_button.text = "Login"
            await self.main_window.error_dialog('Authentication failed', 'Please try again')
            return

        self.user_config['school'] = self.zermelo_school.value.strip()
        self.user_config['account_name'] = self.zermelo_user.value.strip()
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

        print(
            f"Created new zermelo instance as {self.zermelo_user.value} on {self.zermelo_school.value} with teacher={self.zermelo_teacher.value}")

        if not self.main_loaded:
            self.schoolInSchoolYear = self.zermelo.getSchoolInSchoolYear(self.zermelo.getSchoolInSchoolYears())
            self.accounts = self.zermelo.getAccounts(self.schoolInSchoolYear)

            self.main_setup()
            self.main_loaded = True

        self.login_button.enabled = True
        self.login_button.text = "Login"

        self.main()

    async def logout_trigger(self, widget):
        if await self.main_window.confirm_dialog('Confirm logging out', 'Are you sure you want to log out?'):
            self.logout_zermelo()
            await self.main_window.info_dialog('Logged out', 'Successfully logged out')
        else:
            print("Cancelled logging out")

    def logout_zermelo(self):
        pathlib.Path(self.paths.data / 'ZToken').unlink(missing_ok=True)
        self.login_view()

        print("Logged out")

    def compute_scheduler(self, widget):
        asyncio.create_task(self.compute())

    async def compute(self):
        def set_schedules():
            global schedule
            global other_schedule
            schedule = self.zermelo.sort_schedule(username=account1.id, teacher=account1.teacher)
            other_schedule = self.zermelo.sort_schedule(username=account2.id, teacher=account2.teacher)

        await asyncio.sleep(0)  # Yield to event loop briefly
        loop = asyncio.get_event_loop()

        self.compute_button.enabled = False
        self.compute_button.text = "Fetching data..."

        def is_day_later(date1, date2):
            # Extract dates without time
            date1_date_only = date1.date()
            date2_date_only = date2.date()

            # Calculate the difference between the dates
            date_diff = date2_date_only - date1_date_only

            # Check if the difference is exactly one day
            return date_diff >= datetime.timedelta(days=1)

        account1 = self.name1_selection.value

        account2 = self.name2_selection.value

        show_breaks = self.show_breaks.value

        try:
            await loop.run_in_executor(None, set_schedules)

        except ValueError:
            # If zermelo auth expired
            self.logout_zermelo()
            await self.main_window.info_dialog('Session expired', 'Please log in again.')
            self.compute_button.text = "Compute"
            self.compute_button.enabled = True
            return

        if not schedule:
            await self.main_window.error_dialog('No schedule found', 'No schedule found for user 1.')
            self.compute_button.text = "Compute"
            self.compute_button.enabled = True
            return
        if not other_schedule:
            await self.main_window.error_dialog('No schedule found', 'No schedule found for user 2.')
            self.compute_button.text = "Compute"
            self.compute_button.enabled = True
            return

        self.compute_button.text = "Processing data..."

        hours = free_common_hours(schedule, other_schedule, show_breaks)

        self.compute_button.text = "Listing data..."

        self.result_box.clear()

        self.result_box.add(toga.Label(f"Common free hours:", style=Pack(padding=(0, 5), font_size=FontSize.big.value)))
        self.result_box.add(
            toga.Label(
                f"Account 1: {account1.name}\nAccount 2: {account2.name}\nBreaks shown: {'yes' if show_breaks else 'no'}",
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

        if not hours:
            self.result_box.add(toga.Label('\nNo common free hours found.',
                                           style=Pack(padding=(0, 5), font_size=FontSize.large.value)))

        self.compute_button.text = "Compute"
        self.compute_button.enabled = True


def main():
    return CommonFreeHours()
