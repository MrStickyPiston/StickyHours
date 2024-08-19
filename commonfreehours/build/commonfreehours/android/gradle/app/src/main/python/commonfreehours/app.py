"""
Easily check for common free hours in zermelo.
"""
import asyncio
import datetime
import logging
import pathlib
import sys
import traceback
from enum import Enum
from typing import List, Self

import freezegun
import toga
import configparser

from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import toga.platform
from commonfreehours.lang import Lang
from .commonFreeHours import get_accounts, process_appointments, get_common_gaps
from .accountentry import AccountEntry

from .zapi import *
import commonfreehours.utils as utils
from .zapi.zermelo import get_school_year


class FontSize(Enum):
    s = 14
    l = 16
    xl = 19
    xxl = 22

lang = Lang()
_ = lang.translate

@freezegun.freeze_time("2024-6-12")
class CommonFreeHours(toga.App):

    # For except hook
    instance: Self = None

    def __init__(self):
        super().__init__()
        self.main_loaded = False
        self.accounts = []
        self.common_gaps_cache = {}

        self.zermelo = Zermelo()

        logging.basicConfig(level=logging.DEBUG)

    def startup(self):
        logging.info("method startup called")
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

        if (
            self.user_config.get('instance_id', '') == '' or
            self.user_config.get('account_name', '') == '' or
            self.user_config.get('token', '') == ''):
            logging.info(f"Empty value in user in config, logging in again.")
            self.login_view()
        else:
            try:
                self.zermelo.token_login(self.user_config.get('token'), self.user_config.get('instance_id'))
                logging.info(
                    f"Logged in with existing token with account {self.user_config.get('account_name')} on {self.user_config.get('school')}")
                self.main()

            except Exception as e:
                logging.info("Logging in failed")
                logging.debug(f"Logging in error: {e}")
                self.handle_exception(e)
                self.login_view()

        self.main_window.show()

    def handle_exception(self, exception: Exception):
        logging.error(f"Handling exception: {exception}")
        try:
            raise exception
        except ZermeloApiNetworkError:
            self.main_window.error_dialog(_('error.network.title'), _('error.network.message'))
        except ZermeloAuthException:
            self.main_window.error_dialog(_('error.auth.title'), _('error.auth.message'))
            self.logout_zermelo()
            self.login_view()
        except ZermeloApiDataException:
            self.main_window.error_dialog(_('error.data.title'), _('error.data.message'))
        except ZermeloFunctionSettingsError:
            self.main_window.error_dialog(_('error.function_settings.title'), _('error.function_settings.message'))
            self.logout_zermelo()
            self.login_view()
        except ZermeloApiHttpStatusException:
            self.main_window.error_dialog(_('error.http_status.title'), _('error.http_status.message'))
        except:
            # android has no stacktrace dialog
            if utils.platform == "ANDROID":
                self.main_window.error_dialog(_('error.other.title'), _('error.other.message') + "\n\n" + traceback.format_exc())
            else:
                self.main_window.stack_trace_dialog(_('error.other.title'), _('error.other.message'), traceback.format_exc())


    def get_account_options(self):
        #TODO: replace school year
        if self.accounts:
            return self.accounts
        try:
            self.accounts = get_accounts(self.zermelo, get_school_year())
            return self.accounts
        except ZermeloAuthException:
            return []
        except Exception as e:
            self.handle_exception(e)

    def add_entry(self, widget=None, value=None):
        new_entry = AccountEntry(controller=self,
                                 options_func=self.get_account_options,
                                 add_button_translation=_('main.button.remove_entry'),
                                 filter_placeholder_translation=_('main.placeholder.filter_entry'),
                                 value=value
                                 )

        self.entries.append(new_entry)
        self.entry_box.add(new_entry.box)  # Insert before buttons

    def remove_entry(self, entry: AccountEntry):
        self.entries.remove(entry)
        self.entry_box.remove(entry.box)

    def main_setup(self):
        # Main box to hold all widgets
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        self.main_container = toga.ScrollContainer(content=main_box, horizontal=False)

        entries_label = toga.Label(text=_('main.label.entries'), style=Pack(font_size=FontSize.xl.value))
        self.entry_box = toga.Box(style=Pack(direction=COLUMN))
        self.entries: List[AccountEntry] = []

        add_entry_button = toga.Button(_('main.button.add_entry'), on_press=self.add_entry, style=utils.button_style)

        weeks_amount_label = toga.Label(text=_('main.label.weeks_amount'), style=Pack(font_size=FontSize.xl.value))
        self.weeks_amount_input = toga.Selection(items=[1, 2, 3, 4, 5])

        self.compute_button = toga.Button(_('main.button.idle'), on_press=self.compute_scheduler, style=utils.button_style)

        self.result_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))

        # Add elements to the screen
        main_box.add(entries_label)
        main_box.add(self.entry_box)
        main_box.add(add_entry_button)

        main_box.add(weeks_amount_label)
        main_box.add(self.weeks_amount_input)

        main_box.add(self.compute_button)

        if toga.platform.get_current_platform() == 'iOS':
            main_box.add(toga.Button(_('command.logout'), on_press=self.logout_trigger, style=utils.button_style))

        main_box.add(self.result_box)

    def main(self):
        self.main_window.title = self.formal_name

        self.logout_command.enabled = True

        try:
            self.accounts = get_accounts(self.zermelo, get_school_year())
        except Exception as e:
            self.handle_exception(e)

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
            toga.Label(_('auth.school'), style=Pack(font_size=FontSize.l.value)))

        school_box = toga.Box(style=Pack(direction=COLUMN))
        school_box.add(school_info_box)
        school_box.add(self.zermelo_school_input)

        zermelo_box.add(school_box)

        # Zermelo user
        self.zermelo_user_input = toga.TextInput()

        user_info_box = toga.Box(style=Pack(direction=COLUMN))
        user_info_box.add(
            toga.Label(_('auth.user'), style=Pack(font_size=FontSize.l.value)))

        user_box = toga.Box(style=Pack(direction=COLUMN))
        user_box.add(user_info_box)
        user_box.add(self.zermelo_user_input)

        zermelo_box.add(user_box)

        # Zermelo password
        self.zermelo_password = toga.PasswordInput()
        password_info_box = toga.Box(style=Pack(direction=COLUMN))
        password_info_box.add(
            toga.Label(_('auth.password'), style=Pack(font_size=FontSize.l.value)))

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

        try:
            self.zermelo_school_input.value = self.user_config.get('school')
            self.zermelo_user_input.value = self.user_config.get('account_name')
        except Exception as e:
            self.handle_exception(e)

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

        logging.info(
            f"Logging in as {self.zermelo_user_input.value} on {self.zermelo_school_input.value}")

        try:
            await loop.run_in_executor(None, login)
        except ZermeloValueError:
            logging.info(f"Invalid instance id: {self.zermelo_school_input.value.strip()}")
            done()
            await self.main_window.error_dialog(_('auth.message.failed.title'), _('auth.message.failed.instance_id'))

            return
        except ZermeloAuthException:
            logging.info(f"Invalid username or password")
            done()
            await self.main_window.error_dialog(_('auth.message.failed.title'), _('auth.message.failed.credentials'))

            return
        except Exception as e:
            done()
            self.handle_exception(e)
            return

        logging.info("Logged in successfully")

        self.user_config['account_name'] = self.zermelo_user_input.value.strip()
        self.user_config['instance_id'] = self.zermelo_school_input.value.strip()
        self.user_config['token'] = self.zermelo.get_token()

        with open(self.paths.data / 'commonFreeHours.ini', 'w') as f:
            self.config.write(f)

        logging.info("Saved config")

        done()

        self.main()

    async def logout_trigger(self, widget):
        if await self.main_window.confirm_dialog(_('command.logout.confirm.title'),
                                                 _('command.logout.confirm.message')):
            self.logout_zermelo()
            await self.main_window.info_dialog(_('command.logout.success.title'), _('command.logout.success.message'))
        else:
            logging.info("Cancelled logging out")

    def logout_zermelo(self):
        self.zermelo.logout()
        self.user_config['token'] = ''
        self.login_view()

        with open(self.paths.data / 'commonFreeHours.ini', 'w') as f:
            self.config.write(f)

        logging.info("Logged out")

    def compute_scheduler(self, widget):
        asyncio.create_task(self.compute())

    async def compute(self):
        def sync():
            gaps = []

            for v in set(entries):
                logging.info(f"Fetching {v.id}")

                a = self.zermelo.get_current_weeks_appointments(user=v.id, is_teacher=v.teacher, weeks=int(self.weeks_amount_input.value), valid_only=True)
                if not a:
                    self.main_window.error_dialog(_('main.message.no_schedule.title'), _('main.message.no_schedule.message'))
                    break
                logging.info(f"Preprocessing {v.id}")
                g = process_appointments(a)
                if not g:
                    self.main_window.error_dialog(_('main.message.no_gaps.title'), _('main.message.no_gaps.message'))
                    break
                gaps.append(g)

            self.common_gaps_cache = get_common_gaps(*gaps)

        def done():
            self.compute_button.enabled = True
            self.compute_button.text = _('main.button.idle')

        await asyncio.sleep(0)  # Yield to event loop briefly
        loop = asyncio.get_event_loop()

        self.compute_button.enabled = False
        self.compute_button.text = _('main.button.processing')

        entries = []
        ids = []

        # Keep requests down to a minimum by removing duplicates.
        for entry in self.entries:
            if entry.get_value() is None:
                # TODO: notify user
                done()
                return
            elif entry.get_value().id not in ids:
                entries.append(entry.get_value())
                ids.append(entry.get_value().id)

        try:
            await loop.run_in_executor(None, sync)
        except Exception as e:
            # TODO: implement ZermeloApiNetworkError
            done()
            await self.main_window.error_dialog(_('main.message.failed.title'), _('main.message.failed.error') + "\n\n" + str(traceback.format_exc()))
            raise e

        self.compute_button.text = _('main.button.listing')

        self.result_box.clear()

        self.result_box.add(
            toga.Label(_('main.results.header'), style=Pack(font_size=FontSize.xl.value)))

        for entry in entries:
            self.result_box.add(
            toga.Label(
                entry.name,
                style=Pack(font_size=FontSize.s.value)))

        for day in self.common_gaps_cache.keys():
            if not self.common_gaps_cache.get(day):
                continue

            self.result_box.add(toga.Label(self.common_gaps_cache.get(day)[0][1][0].strftime('\n%A %d %B %Y'),
                                           style=Pack(font_size=FontSize.l.value)))
            for gap in self.common_gaps_cache.get(day):
                self.result_box.add(toga.Label(
                    f"{gap[1][0].strftime('%H:%M')} - {gap[1][1].strftime('%H:%M')} ({gap[1][1] - gap[1][0]})",
                    style=Pack(font_size=FontSize.s.value)))

        if not self.common_gaps_cache:
            self.result_box.add(toga.Label(f'\n{_('main.results.none')}', style=Pack(font_size=FontSize.l.value)))

        self.compute_button.text = _('main.button.idle')
        self.compute_button.enabled = True


def main():
    return CommonFreeHours()