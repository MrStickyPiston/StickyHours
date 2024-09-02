import toga
from toga.style import Pack
from toga.constants import ROW
from travertino.constants import COLUMN

from stickyhours import utils


class AccountEntry:
    def __init__(self, controller, options_func, add_button_translation, filter_placeholder_translation, value=None):
        self.controller = controller
        self.options_func = options_func

        # Selector with items
        self.selector = toga.Selection(items=self.options_func(), accessor='name', style=Pack(flex=1))


        # Text input to filter selector
        self.filter_input = toga.TextInput(on_change=self.filter_selector, placeholder=filter_placeholder_translation, style=Pack(flex=1))
        if value:
            self.filter_input.value = value

        # Remove button
        self.remove_button = toga.Button(add_button_translation, on_press=self.remove_entry, style=utils.button_style)

        # Entry row box
        self.box = toga.Box(
            children=[self.filter_input, self.selector, self.remove_button],
            style=Pack(direction=COLUMN,padding_bottom=10)
        )

    def filter_selector(self, widget):
        filtered_items = [option for option in self.options_func() if widget.value.lower() in option.get('name').lower()]
        self.selector.items = filtered_items

    def remove_entry(self, widget):
        self.controller.remove_entry(self)

    def get_value(self):
        return self.selector.value