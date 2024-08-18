import toga
from attr import attributes
from toga.style import Pack
from toga.constants import ROW
from travertino.constants import COLUMN

from commonfreehours import utils


class AccountEntry:
    def __init__(self, controller, options_func, value=None):
        self.controller = controller
        self.options_func = options_func

        # Selector with items
        self.selector = toga.Selection(items=self.options_func(), accessor='name', style=Pack(flex=1))


        # Text input to filter selector
        self.filter_input = toga.TextInput(on_change=self.filter_selector, placeholder="Filter...", style=Pack(flex=1))
        if value:
            print('v,', value)
            self.filter_input.value = value

        # Remove button
        self.remove_button = toga.Button('Remove', on_press=self.remove_entry, style=utils.button_style)

        # Entry row box
        self.box = toga.Box(
            children=[self.filter_input, self.selector, self.remove_button],
            style=Pack(direction=COLUMN,padding_bottom=10)
        )

    def filter_selector(self, widget):
        filtered_items = [option for option in self.options_func() if widget.value.lower() in option.get('name').lower()]
        print(filtered_items)
        self.selector.items = filtered_items

    def remove_entry(self, widget):
        self.controller.remove_entry(self)

    def get_value(self):
        return self.selector.value