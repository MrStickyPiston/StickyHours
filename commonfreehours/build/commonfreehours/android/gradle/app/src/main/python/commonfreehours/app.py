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
from commonfreehours.lang import Lang


class FontSize(Enum):
    small = 14
    large = 16
    big = 22


class CommonFreeHours(toga.App):
    def __init__(self):
        super().__init__()
        self.main_loaded = False
        self.accounts = []

        global _

        self.lang = Lang()
        _ = self.lang.translate

    def startup(self):
        # Main window of the application
        self.main_window = toga.MainWindow(title=self.formal_name)

        # Setup command for logout
        self.account_group = toga.command.Group(
            text=_('command.group.account'),
        )

        self.logout_command = toga.Command(
            self.logout_trigger,
            text=_('command.logout'),
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
        compare_box = toga.Box(style=Pack(direction=COLUMN))

        # Account name 1
        account1_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 0, 10, 0)))

        name1_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))

        name1_box.add(
            toga.Label(_('main.accounts.1.title'), style=Pack(font_size=FontSize.large.value)))

        self.name1_input = toga.TextInput(
            style=Pack(flex=1, padding=(0, 5)),
            on_change=self.on_change_query_1
        )

        name1_box.add(toga.Label(_('main.accounts.search'), style=Pack(padding=(0, 5), font_size=FontSize.small.value)))

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

        name2_box.add(
            toga.Label(_('main.accounts.2.title'), style=Pack(font_size=FontSize.large.value)))

        self.name2_input = toga.TextInput(
            style=Pack(flex=1, padding=(0, 5)),
            on_change=self.on_change_query_2
        )

        name2_box.add(toga.Label(_('main.accounts.search'), style=Pack(padding=(0, 5), font_size=FontSize.small.value)))

        name2_box.add(self.name2_input)

        self.name2_selection = toga.Selection(items=self.accounts,
                                              accessor='name',
                                              style=Pack(flex=1, padding=(0, 5)))
        name2_box.add(self.name2_selection)
        account2_box.add(name2_box)

        compare_box.add(account2_box)

        # Breaks
        breaks_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 0, 10, 0)))

        breaks_box.add(toga.Label(_('main.breaks.header'), style=Pack(padding=(0, 5), font_size=FontSize.large.value)))

        self.show_breaks = toga.Switch('', style=Pack(padding=(0, 5), font_size=FontSize.large.value))
        show_breaks_box = toga.Box(style=Pack(direction=ROW, padding=(0, 5)))
        show_breaks_box.add(
            toga.Label(_('main.breaks.show'), style=Pack(padding=(0, 5), font_size=FontSize.small.value)))
        show_breaks_box.add(self.show_breaks)
        breaks_box.add(show_breaks_box)

        compare_box.add(breaks_box)

        # Compute button
        self.compute_button = toga.Button(_('main.button.idle'), on_press=self.compute_scheduler)

        # Result
        self.result_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))

        result_label = toga.Label(_('main.results.placeholder'), style=Pack(flex=1))
        self.result_box.add(result_label)

        # Add Compare section to main box
        main_box.add(compare_box)
        main_box.add(self.compute_button)
        main_box.add(self.result_box)

    def main(self):
        self.main_window.title = self.formal_name

        self.logout_command.enabled = True

        self.main_window.content = self.main_container

    def login_setup(self):
        self.login_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # Zermelo credentials section
        zermelo_box = toga.Box(style=Pack(direction=COLUMN))

        # Zermelo school
        self.zermelo_school_input = toga.TextInput()

        school_info_box = toga.Box(style=Pack(direction=COLUMN))
        school_info_box.add(
            toga.Label(_('auth.school'), style=Pack(font_size=FontSize.large.value)))

        school_box = toga.Box(style=Pack(direction=COLUMN))
        school_box.add(school_info_box)
        school_box.add(self.zermelo_school_input)

        zermelo_box.add(school_box)

        # Zermelo user
        self.zermelo_user_input = toga.TextInput()

        user_info_box = toga.Box(style=Pack(direction=COLUMN))
        user_info_box.add(
            toga.Label(_('auth.user'), style=Pack(font_size=FontSize.large.value)))

        user_box = toga.Box(style=Pack(direction=COLUMN))
        user_box.add(user_info_box)
        user_box.add(self.zermelo_user_input)

        zermelo_box.add(user_box)

        # Zermelo password
        self.zermelo_password = toga.PasswordInput()
        password_info_box = toga.Box(style=Pack(direction=COLUMN))
        password_info_box.add(
            toga.Label(_('auth.password'), style=Pack(font_size=FontSize.large.value)))

        password_box = toga.Box(style=Pack(direction=COLUMN))
        password_box.add(password_info_box)
        password_box.add(self.zermelo_password)

        zermelo_box.add(password_box)

        self.zermelo_teacher = toga.Switch('', style=Pack(font_size=FontSize.large.value))
        is_teacherz_box = toga.Box(style=Pack(direction=ROW))
        is_teacherz_box.add(
            toga.Label(_('auth.is_teacher'), style=Pack(font_size=FontSize.small.value)))
        is_teacherz_box.add(self.zermelo_teacher)
        zermelo_box.add(is_teacherz_box)

        self.login_button = toga.Button(_('auth.button.idle'), on_press=self.login_scheduler)

        # Add Zermelo section to main box
        self.login_box.add(zermelo_box)

        self.login_box.add(self.login_button)

    def login_view(self):
        self.main_window.title = f"{_('auth.window.title')} - {self.formal_name}"

        self.logout_command.enabled = False

        self.zermelo_school_input.value = self.user_config.get('school')
        self.zermelo_user_input.value = self.user_config.get('account_name')
        self.zermelo_teacher.value = self.user_config.get('teacher') == 'True'

        self.main_window.content = self.login_box

    def login_scheduler(self, widget):
        asyncio.create_task(self.login())

    async def login(self):
        def login_test():
            zapi.zermelo(
                school=self.zermelo_school_input.value.strip(),
                username=self.zermelo_user_input.value.strip(),
                teacher=self.zermelo_teacher.value,
                password=self.zermelo_password.value,
                version=3,
                token_file=self.paths.data / 'ZToken',
            )

        await asyncio.sleep(0)  # Yield to event loop briefly
        loop = asyncio.get_event_loop()

        if self.zermelo_school_input.value == '' or self.zermelo_user_input.value == '' or self.zermelo_password.value == '':
            await self.main_window.error_dialog(_('auth.message.failed.title'), _('auth.message.failed.message.fields'))
            return

        self.login_button.enabled = False
        self.login_button.text = _('auth.button.progress')

        print(
            f"Logging in as {self.zermelo_user_input.value} on {self.zermelo_school_input.value} with teacher={self.zermelo_teacher.value}")

        try:
            await loop.run_in_executor(None, login_test)
        except (RuntimeError, ValueError) as e:
            print(e)
            self.login_button.enabled = True
            self.login_button.text = _('auth.button.idle')
            await self.main_window.error_dialog(_('auth.message.failed.title'), _('auth.message.failed.message'))
            return

        self.user_config['school'] = self.zermelo_school_input.value.strip()
        self.user_config['account_name'] = self.zermelo_user_input.value.strip()
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
            f"Created new zermelo instance as {self.zermelo_user_input.value} on {self.zermelo_school_input.value} with teacher={self.zermelo_teacher.value}")

        if not self.main_loaded:
            self.schoolInSchoolYear = self.zermelo.getSchoolInSchoolYear(self.zermelo.getSchoolInSchoolYears())
            self.accounts = self.zermelo.getAccounts(self.schoolInSchoolYear)

            self.main_setup()
            self.main_loaded = True

        self.login_button.enabled = True
        self.login_button.text = _('auth.button.idle')

        self.main()

    async def logout_trigger(self, widget):
        if await self.main_window.confirm_dialog(_('command.logout.confirm.title'),
                                                 _('command.logout.confirm.message')):
            self.logout_zermelo()
            await self.main_window.info_dialog(_('command.logout.success.title'), _('command.logout.success.message'))
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

        async def error(user):
            await self.main_window.error_dialog(
                _('main.error.no-schedule.title'),
                _('main.error.no-schedule.message').format(user)
            )

            self.compute_button.text = _('main.button.idle')
            self.compute_button.enabled = True

        await asyncio.sleep(0)  # Yield to event loop briefly
        loop = asyncio.get_event_loop()

        self.compute_button.enabled = False
        self.compute_button.text = _('main.button.fetching')

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

        if account1 is None:
            await error(
                self.name1_input.value.strip() if self.name1_input.value.strip() != '' else _('main.accounts.1.title'))
            return
        if account2 is None:
            await error(
                self.name2_input.value.strip() if self.name1_input.value.strip() != '' else _('main.accounts.2.title'))
            return

        try:
            await loop.run_in_executor(None, set_schedules)

        except ValueError:
            # If zermelo auth expired
            self.logout_zermelo()
            await self.main_window.info_dialog(_('auth.error.expired.title'), _('auth.error.expired.message'))
            self.compute_button.text = _('main.button.idle')
            self.compute_button.enabled = True
            return

        if not schedule:
            await error(account1.name)
            return
        if not other_schedule:
            await error(account2.name)
            return

        self.compute_button.text = _('main.button.processing')

        hours = free_common_hours(schedule, other_schedule, show_breaks)

        self.compute_button.text = _('main.button.listing')

        self.result_box.clear()

        self.result_box.add(
            toga.Label(_('main.results.header'), style=Pack(font_size=FontSize.big.value)))
        self.result_box.add(
            toga.Label(
                f"{_('main.accounts.1.title')}: {account1.name}\n{_('main.accounts.2.title')}: {account2.name}\n{_('main.breaks.show')}: {_('common.yes') if show_breaks else _('common.no')}",
                style=Pack(font_size=FontSize.small.value)))

        day = datetime.datetime.fromtimestamp(datetime.MINYEAR)

        for hour in hours:
            if is_day_later(day, hour.get('start')):
                day = hour.get('start')
                self.result_box.add(toga.Label(hour.get('start').strftime('\n%A %d %B %Y'),
                                               style=Pack(font_size=FontSize.large.value)))

            if not hour.get('break'):
                self.result_box.add(toga.Label(
                    f"{hour.get('start').strftime('%H:%M')} - {hour.get('end').strftime('%H:%M')} ({hour.get('end') - hour.get('start')})",
                    style=Pack(font_size=FontSize.small.value)))
            elif show_breaks:
                self.result_box.add(toga.Label(
                    f"[{_('main.results.break.indicator.text')}] {hour.get('start').strftime('%H:%M')} - {hour.get('end').strftime('%H:%M')} ({hour.get('end') - hour.get('start')})",
                    style=Pack(font_size=FontSize.small.value)))

        if not hours:
            self.result_box.add(toga.Label(f'\n{_('main.results.none')}',
                                           style=Pack(font_size=FontSize.large.value)))

        self.compute_button.text = _('main.button.idle')
        self.compute_button.enabled = True


def main():
    return CommonFreeHours()
