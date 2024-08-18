"""
Easily check for common free hours in zermelo.
"""
import asyncio
import datetime
import logging
import pathlib
import traceback
from enum import Enum

import toga
import configparser

from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import toga.platform
from commonfreehours.lang import Lang
from .commonFreeHours import get_accounts
from .accountentry import AccountEntry

from .zapi import *
import commonfreehours.utils as utils
from .zapi.zermelo import get_school_year


class FontSize(Enum):
    small = 14
    large = 16
    big = 22


class CommonFreeHours(toga.App):
    def __init__(self):
        super().__init__()
        self.main_loaded = False
        self.accounts = []

        self.zermelo = Zermelo()

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)

        global _

        self.lang = Lang()
        _ = self.lang.translate

    def startup(self):
        print(self.paths.data)
        self.logger.info("method startup called")
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

        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.read(self.paths.data / 'commonFreeHours.ini')

        if 'user' not in self.config.sections():
            self.config['user'] = {}

        self.user_config = self.config['user']

        self.login_setup()
        self.main_setup()

        if not self.user_config.get('instance_id') or not self.user_config.get('account_name') or not self.user_config.get('token'):
            self.logger.info(f"None value in user in config, logging in again.")
            self.login_view()
        else:
            try:
                self.zermelo.token_login(self.user_config.get('token'), self.user_config.get('instance_id'))
                self.main()
                print(
                    f"Used existing zermelo instance as {self.user_config.get('account_name')} on {self.user_config.get('school')} with teacher={self.user_config.get('teacher')}")

            except ZermeloAuthException as e:
                self.logger.info("Logging in failed")
                self.logger.debug(f"Logging in error: {e}")
                # Token invalid, log in again
                pass

        self.main_window.show()

    async def on_change_query_1(self, widget: toga.TextInput):
        options = [option for option in self.accounts if widget.value.lower() in option.get('name').lower()]
        self.name1_selection.items = options

    async def on_change_query_2(self, widget: toga.TextInput):
        options = []
        self.name2_selection.items = options

    def get_account_options(self):
        #TODO: replace school year
        if self.accounts:
            return self.accounts
        try:
            self.accounts = get_accounts(self.zermelo, 2023)
            return self.accounts
        except ZermeloAuthException:
            return []

    def add_entry(self, widget=None, value=None):
        new_entry = AccountEntry(controller=self, options_func=self.get_account_options, value=value)

        self.entries.append(new_entry)
        self.entry_box.add(new_entry.box)  # Insert before buttons

    def remove_entry(self, entry: AccountEntry):
        self.entries.remove(entry)
        self.entry_box.remove(entry.box)

    def main_setup(self):
        # Main box to hold all widgets
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        self.main_container = toga.ScrollContainer(content=main_box, horizontal=False)

        self.entry_box = toga.Box(style=Pack(direction=COLUMN))
        self.entries = []

        add_button = toga.Button('Add Entry', on_press=self.add_entry, style=utils.button_style)

        main_box.add(self.entry_box)
        main_box.add(add_button)

        # Compute button
        self.compute_button = toga.Button(_('main.button.idle'), on_press=self.compute_scheduler, style=utils.button_style)

        # Result
        self.result_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))

        result_label = toga.Label(_('main.results.placeholder'), style=Pack(flex=1))
        self.result_box.add(result_label)

        # Add Compare section to main box
        main_box.add(self.compute_button)

        if toga.platform.get_current_platform() == 'iOS':
            main_box.add(toga.Button(_('command.logout'), on_press=self.logout_trigger, style=utils.button_style))

        main_box.add(self.result_box)

    def main(self):
        self.main_window.title = self.formal_name

        self.logout_command.enabled = True

        self.accounts = get_accounts(self.zermelo, 2023)

        if not self.entries:
            self.add_entry(value=self.zermelo.get_user().get('code'))

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

        self.login_button = toga.Button(_('auth.button.idle'), on_press=self.login_scheduler, style=utils.button_style)
        self.login_help_button = toga.Button(_('auth.button.help'), on_press=self.login_help, style=utils.button_style)

        # Add Zermelo section to main box
        self.login_box.add(zermelo_box)

        self.login_box.add(self.login_button)
        self.login_box.add(self.login_help_button)

    def login_view(self):
        self.main_window.title = f"{_('auth.window.title')} - {self.formal_name}"

        self.logout_command.enabled = False

        self.zermelo_school_input.value = self.user_config.get('school')
        self.zermelo_user_input.value = self.user_config.get('account_name')

        self.main_window.content = self.login_box

    async def login_help(self, widget):
        utils.open_url(self.app.home_page.rstrip('/') + '/' + 'login-help')
        pass

    def login_scheduler(self, widget):
        asyncio.create_task(self.login_task())

    async def login_task(self):
        def login():
            self.zermelo.password_login(
                self.zermelo_school_input.value.strip(),
                self.zermelo_user_input.value.strip(),
                self.zermelo_password.value
            )

        def done():
            self.login_button.enabled = True
            self.login_button.text = _('auth.button.idle')

        await asyncio.sleep(0)  # Yield to event loop briefly
        loop = asyncio.get_event_loop()

        if self.zermelo_school_input.value == '' or self.zermelo_user_input.value == '' or self.zermelo_password.value == '':
            await self.main_window.error_dialog(_('auth.message.failed.title'), _('auth.message.failed.fields'))
            return

        self.login_button.enabled = False
        self.login_button.text = _('auth.button.progress')

        self.logger.info(
            f"Logging in as {self.zermelo_user_input.value} on {self.zermelo_school_input.value}")

        try:
            await loop.run_in_executor(None, login)
        except ZermeloValueError:
            self.logger.info(f"Invalid instance id: {self.zermelo_school_input.value.strip()}")
            done()
            await self.main_window.error_dialog(_('auth.message.failed.title'), _('auth.message.failed.instance_id'))

            return
        except ZermeloAuthException:
            self.logger.info(f"Invalid username or password")
            done()
            await self.main_window.error_dialog(_('auth.message.failed.title'), _('auth.message.failed.credentials'))

            return
        except Exception as e:
            # TODO: implement ZermeloApiNetworkError
            done()
            await self.main_window.stack_trace_dialog(_('auth.message.failed.title'), _('auth.message.failed.error'), str(traceback.format_exc()))
            raise e

        self.user_config['account_name'] = self.zermelo_user_input.value.strip()
        self.user_config['instance_id'] = self.zermelo_school_input.value.strip()
        self.user_config['token'] = self.zermelo.get_token()

        print("Logged in successfully")

        with open(self.paths.data / 'commonFreeHours.ini', 'w') as f:
            self.config.write(f)

        print("Saved config")

        done()

        self.main()

    async def logout_trigger(self, widget):
        if await self.main_window.confirm_dialog(_('command.logout.confirm.title'),
                                                 _('command.logout.confirm.message')):
            self.logout_zermelo()
            await self.main_window.info_dialog(_('command.logout.success.title'), _('command.logout.success.message'))
        else:
            print("Cancelled logging out")

    def logout_zermelo(self):
        self.zermelo.logout()
        self.user_config['token'] = None
        self.login_view()

        print("Logged out")

    def compute_scheduler(self, widget):
        asyncio.create_task(self.compute())

    async def compute(self):
        def set_schedules():
            global schedule
            global other_schedule

            schedule = self.zermelo.sort_schedule(username=account1.id, teacher=account1.teacher, only_valid=True)
            other_schedule = self.zermelo.sort_schedule(username=account2.id, teacher=account2.teacher, only_valid=True)

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
