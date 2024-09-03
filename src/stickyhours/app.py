"""
Easily check for common free hours in zermelo.
"""
import asyncio
import logging
import time
import traceback
from asyncio import timeout
from enum import Enum
from typing import List, Self

import freezegun
import toga
import configparser

from toga.style import Pack
from toga.style.pack import COLUMN
import toga.platform

from stickyhours.lang import Lang
from .commonFreeHours import get_accounts, process_appointments, get_common_gaps
from .accountentry import AccountEntry

from .zapi import *
import stickyhours.utils as utils
from .zapi.zermelo import get_school_year

from babel.dates import format_date


class FontSize(Enum):
    s = 14
    l = 16
    xl = 19
    xxl = 22

lang = Lang()
_ = lang.translate

class stickyhours(toga.App):

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
        self.config.read(self.paths.data / 'stickyhours.ini')

        if 'user' not in self.config.sections():
            self.config['user'] = {}

        self.user_config = self.config['user']

        self.login_setup()
        self.main_setup()

        if (
            self.user_config.get('instance_id', '') == '' or
            self.user_config.get('token', '') == ''):
            logging.info(f"Empty value in user in config, logging in again.")
            self.login_view()
        else:
            try:
                self.zermelo.token_login(self.user_config.get('token'), self.user_config.get('instance_id'))
                logging.info(
                    f"Logged in with existing token with account on {self.user_config.get('instance_id')}")
                self.get_account_options()
                self.main()

            except ZermeloAuthException:
                logging.info("Auth error, token invalid")
                self.login_view()

            except Exception as e:
                logging.info("Logging in failed")
                logging.debug(f"Logging in error: {e}")
                self.handle_exception(e, show_error_view=True)

        self.main_window.show()

    def handle_exception(self, exception: Exception, show_error_view: bool = False):
        logging.error(f"Handling exception: {exception}")

        show_traceback = False

        try:
            raise exception
        except ZermeloApiNetworkError:
            self.main_window.error_dialog(_('error.network.title'), _('error.network.message'))
            message = _('error.network.message')
        except ZermeloAuthException:
            self.main_window.error_dialog(_('error.auth.title'), _('error.auth.message'))
            self.logout_zermelo()
            self.login_view()
        except ZermeloApiDataException:
            self.main_window.error_dialog(_('error.data.title'), _('error.data.message'))
            message = _('error.data.message')
        except ZermeloFunctionSettingsError:
            self.main_window.error_dialog(_('error.function_settings.title'), _('error.function_settings.message').format(exception.setting, exception.value, exception.required_value, exception.endpoint))
            message = _('error.function_settings.message').format(exception.setting, exception.value, exception.required_value, exception.endpoint)
        except ZermeloApiHttpStatusException:
            self.main_window.error_dialog(_('error.http_status.title'), _('error.http_status.message'))
            message = _('error.http_status.message')
            show_traceback = True
        except:
            # android has no stacktrace dialog
            if utils.platform == "ANDROID":
                self.main_window.error_dialog(_('error.other.title'), _('error.other.message') + "\n\n" + traceback.format_exc())
            else:
                self.main_window.stack_trace_dialog(_('error.other.title'), _('error.other.message'), traceback.format_exc())

            message = _('error.other.message')
            show_traceback = True
        finally:
            if show_error_view:
                self.error_view(message, show_traceback)


    def get_account_options(self):
        if self.accounts:
            return self.accounts
        try:
            self.accounts = get_accounts(self.zermelo, get_school_year())
            return self.accounts
        except ZermeloAuthException:
            return []
        except Exception as e:
            raise e

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

        self.compute_button = toga.Button(_('main.button.idle'), on_press=self.compute, style=utils.button_style)

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

        if not self.entries:
            self.add_entry(value=self.zermelo.get_user().get('code'))

        self.main_window.content = self.main_container

    def login_setup(self):
        async def help_portal_id(widget):
            utils.open_url(self.app.home_page + '#faq-zermelo-portal-id')

        async def help_linkcode(widget):
            utils.open_url(self.app.home_page + '#faq-zermelo-get-linkcode-for-login')

        self.login_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # Zermelo credentials section
        zermelo_box = toga.Box(style=Pack(direction=COLUMN))

        # Zermelo school
        self.zermelo_school_input = toga.TextInput(style=Pack(flex=1))
        wrapper_input_school = toga.Box()

        wrapper_input_school.add(self.zermelo_school_input)
        wrapper_input_school.add(toga.Box(children=[
            toga.Button(
                text='ⓘ',
                style=Pack(flex=1, width=utils.icon_button_size, height=utils.icon_button_size),
                on_press=help_portal_id
            )
        ]))

        school_info_box = toga.Box(style=Pack(direction=COLUMN))
        school_info_box.add(
            toga.Label(_('auth.school'), style=Pack(font_size=FontSize.l.value)))

        school_box = toga.Box(style=Pack(direction=COLUMN))
        school_box.add(school_info_box)
        school_box.add(wrapper_input_school)

        zermelo_box.add(school_box)

        # Zermelo password
        self.zermelo_linkcode = toga.PasswordInput(style=Pack(flex=1))
        wrapper_input_linkcode = toga.Box()

        wrapper_input_linkcode.add(self.zermelo_linkcode)
        wrapper_input_linkcode.add(toga.Box(children=[
            toga.Button(
                text='ⓘ',
                style=Pack(flex=1, width=utils.icon_button_size, height=utils.icon_button_size),
                on_press=help_linkcode
            )
        ]))
        linkcode_info_box = toga.Box(style=Pack(direction=COLUMN))
        linkcode_info_box.add(
            toga.Label(_('auth.linkcode'), style=Pack(font_size=FontSize.l.value)))

        linkcode_box = toga.Box(style=Pack(direction=COLUMN))
        linkcode_box.add(linkcode_info_box)
        linkcode_box.add(wrapper_input_linkcode)

        zermelo_box.add(linkcode_box)

        self.login_button = toga.Button(_('auth.button.idle'), on_press=self.login_task, style=utils.button_style)
        self.login_help_button = toga.Button(_('auth.button.help'), on_press=self.login_help, style=utils.button_style)

        # Add Zermelo section to main box
        self.login_box.add(zermelo_box)

        self.login_box.add(self.login_button)
        self.login_box.add(self.login_help_button)

    def login_view(self):
        self.main_window.title = f"{_('auth.window.title')} - {self.formal_name}"

        self.logout_command.enabled = False

        try:
            self.zermelo_linkcode.value = ""
            self.zermelo_school_input.value = self.user_config.get('instance_id')
        except Exception as e:
            self.handle_exception(e)

        self.main_window.content = self.login_box

    def error_view(self, message, show_traceback):
        self.main_window.title = f"{_('error.window.title')} - {self.formal_name}"

        self.logout_command.enabled = True

        error_box = toga.Box(style=Pack(flex=1, direction=COLUMN))

        error_text = toga.MultilineTextInput(value=message, readonly=True, style=Pack(flex=1, font_size=FontSize.s.value, padding=10))

        if show_traceback:
            error_text.value += "\n\n" + _('error.window.error_below') + "\n\n" + traceback.format_exc()

        error_box.add(error_text)

        self.main_window.content = error_box

    async def login_help(self, widget):
        utils.open_url(self.app.home_page.rstrip('/') + '#faq-how-to-log-in')
        pass

    async def login_task(self, widget=None):
        def done():
            self.login_button.enabled = True
            self.login_button.text = _('auth.button.idle')

        if self.zermelo_school_input.value == '' or self.zermelo_linkcode.value == '':
            await self.main_window.error_dialog(_('auth.message.failed.title'), _('auth.message.failed.fields'))
            return

        self.login_button.enabled = False
        self.login_button.text = _('auth.button.progress')

        logging.info(
            f"Logging in on {self.zermelo_school_input.value}")

        try:
            await asyncio.wait_for(
                self.loop.run_in_executor(
                    None,
                    self.zermelo.code_login,
                    self.zermelo_linkcode.value, self.zermelo_school_input.value
                ),
                timeout = 20
            )

            await asyncio.wait_for(
                self.loop.run_in_executor(
                    None,
                    self.get_account_options()
                ),
                timeout = 20
            )

        except asyncio.TimeoutError:
            # Handle timeout
            done()
            await self.main_window.error_dialog(_('error.timeout.title'), _('error.timeout.message'))
            return
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
            self.zermelo.logout()
            return

        logging.info("Logged in successfully")

        self.user_config['instance_id'] = self.zermelo_school_input.value.strip()
        self.user_config['token'] = self.zermelo.get_token()

        try:
            self.paths.data.mkdir(parents=True, exist_ok=True)

            with open(self.paths.data / 'stickyhours.ini', 'w') as f:
                self.config.write(f)
        except Exception as e:
            done()
            self.handle_exception(e)
            self.zermelo.logout()
            return

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
        self.accounts = []
        self.zermelo.logout()
        self.user_config['token'] = ''
        self.login_view()

        with open(self.paths.data / 'stickyhours.ini', 'w') as f:
            self.config.write(f)

        logging.info("Logged out")

    async def compute(self, widget=None):
        def done():
            self.compute_button.enabled = True
            self.compute_button.text = _('main.button.idle')

        self.compute_button.enabled = False
        self.compute_button.text = _('main.button.processing')

        entries = []
        ids = []

        # Keep requests down to a minimum by removing duplicates.
        for entry in self.entries:
            if entry.get_value() is None:
                await self.main_window.error_dialog(_('main.message.no_schedule_user.title'), _('main.message.no_schedule_user.message'))
                done()
                return
            elif entry.get_value().id not in ids:
                entries.append(entry.get_value())
                ids.append(entry.get_value().id)

        try:
            gaps = []

            for v in set(entries):
                logging.info(f"Fetching {v.id}")
                self.compute_button.text = _('main.button.fetching.user').format(v.id)

                a = await asyncio.wait_for(self.loop.run_in_executor(None, self.zermelo.get_current_weeks_appointments, v.id, v.teacher, int(self.weeks_amount_input.value), True), timeout=20)

                if not a:
                    # no schedule found
                    break
                logging.info(f"Processing {v.id}")
                self.compute_button.text = _('main.button.processing.user').format(v.id)
                g = process_appointments(a)
                if not g:
                    # no gaps are found for this user
                    break
                gaps.append(g)

            self.common_gaps_cache = get_common_gaps(*gaps)

        except asyncio.TimeoutError:
            # Handle timeout
            done()
            await self.main_window.error_dialog(_('error.timeout.title'), _('error.timeout.message'))
            return
        except Exception as e:
            done()
            self.handle_exception(e)
            return

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

            self.result_box.add(toga.Label("\n" + format_date(self.common_gaps_cache.get(day)[0][1][0], format='full', locale=lang.lang),
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
    return stickyhours()