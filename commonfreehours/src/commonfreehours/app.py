"""
Easily check for common free hours in zermelo.
"""
from enum import Enum

import toga
import zermeloapi
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from commonfreehours.commonFreeHours import free_common_hours


class FontSize(Enum):
    small = 12
    large = 16
    big = 22


class CommonFreeHours(toga.App):
    def __init__(self):
        super().__init__()

    def startup(self):
        # Main window of the application
        self.main_window = toga.MainWindow(title=self.formal_name)

        # Main box to hold all widgets
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # Zermelo credentials section
        zermelo_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))
        zermelo_box.add(toga.Label('Zermelo Credentials', style=Pack(padding=(0, 5, 10, 5), font_size=FontSize.big.value)))

        # Zermelo school
        self.zermelo_school = toga.TextInput(style=Pack(flex=1, padding=(0, 5)))
        zermelo_school_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))
        zermelo_school_box.add(toga.Label('Zermelo school: (organization):', style=Pack(padding=(0, 5), font_size=FontSize.large.value)))
        zermelo_school_box.add(self.zermelo_school)
        zermelo_box.add(zermelo_school_box)

        # Zermelo user
        self.zermelo_user = toga.TextInput(style=Pack(flex=1, padding=(0, 5)))
        zermelo_user_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))
        zermelo_user_box.add(toga.Label('Zermelo account name:', style=Pack(padding=(0, 5), font_size=FontSize.large.value)))
        zermelo_user_box.add(self.zermelo_user)
        zermelo_box.add(zermelo_user_box)

        # Zermelo password
        self.zermelo_password = toga.PasswordInput(style=Pack(flex=1, padding=(0, 5)))
        zermelo_password_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))
        zermelo_password_box.add(toga.Label('Zermelo account password:', style=Pack(padding=(0, 5), font_size=FontSize.large.value)))
        zermelo_password_box.add(self.zermelo_password)
        zermelo_box.add(zermelo_password_box)

        self.zermelo_teacher = toga.Switch('', style=Pack(padding=(0, 5), font_size=FontSize.large.value))
        is_teacherz_box = toga.Box(style=Pack(direction=ROW, padding=(0, 5)))
        is_teacherz_box.add(toga.Label('Account is a teacher account:', style=Pack(padding=(0, 5), font_size=FontSize.small.value)))
        is_teacherz_box.add(self.zermelo_teacher)
        zermelo_box.add(is_teacherz_box)

        # Add Zermelo section to main box
        main_box.add(zermelo_box)

        # Compare section
        compare_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))
        compare_box.add(toga.Label('Compare', style=Pack(padding=(0, 5, 10, 5), font_size=FontSize.big.value)))

        # Account name 1
        account1_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 0, 10, 0)))

        self.name1_input = toga.TextInput(style=Pack(flex=1, padding=(0, 5)))
        name1_box = toga.Box(style=Pack(direction=COLUMN, padding=(0, 5)))
        name1_box.add(toga.Label('Account 1', style=Pack(padding=(0, 5), font_size=FontSize.large.value)))
        name1_box.add(self.name1_input)
        account1_box.add(name1_box)

        self.is_teacher1 = toga.Switch('', style=Pack(padding=(0, 5), font_size=FontSize.large.value))
        is_teacher1_box = toga.Box(style=Pack(direction=ROW, padding=(0, 5)))
        is_teacher1_box.add(toga.Label('Account 1 is a teacher account:', style=Pack(padding=(0, 5), font_size=FontSize.small.value)))
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
        is_teacher2_box.add(toga.Label('Account 2 is a teacher account:', style=Pack(padding=(0, 5), font_size=FontSize.small.value)))
        is_teacher2_box.add(self.is_teacher2)
        account2_box.add(is_teacher2_box)

        compare_box.add(account2_box)

        # Compute button
        self.compute_button = toga.Button('Compute', on_press=self.compute, style=Pack(padding=(0, 5)))

        # Result label
        self.result_label = toga.Label('Result will be shown here', style=Pack(padding=(0, 5)))

        # Add Compare section to main box
        main_box.add(compare_box)
        main_box.add(self.compute_button)
        main_box.add(self.result_label)

        # Set the main window's content
        self.main_window.content = main_box
        self.main_window.show()

    async def compute(self, widget):
        zermelo_school = self.zermelo_school.value
        zermelo_user = self.zermelo_user.value
        zermelo_password = self.zermelo_password.value
        zermelo_is_teacher = self.zermelo_teacher.value

        name1 = self.name1_input.value
        is_teacher1 = self.is_teacher1.value

        name2 = self.name2_input.value
        is_teacher2 = self.is_teacher2.value

        zermelo = zermeloapi.zermelo(
            zermelo_school,
            zermelo_user,
            zermelo_password,
            teacher=zermelo_is_teacher,
            version=3
        )

        schedule = zermelo.sort_schedule(username=name1, teacher=is_teacher1)
        other_schedule = zermelo.sort_schedule(username=name2, teacher=is_teacher2)

        hours = free_common_hours(schedule, other_schedule)

        self.result_label.text = f"Common free hours ({name1} and {name2}):\n\n"

        for hour in hours:
            if hour.get('break'):
                self.result_label.text += f"[BREAK] {hour.get('start')} - {hour.get('end')} ({hour.get('end') - hour.get('start')})\n"
            else:
                self.result_label.text += f"{hour.get('start')} - {hour.get('end')} ({hour.get('end') - hour.get('start')})\n"

def main():
    return CommonFreeHours()
