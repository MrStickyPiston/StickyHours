import toga
import toga_iOS.window
from rubicon.objc import ObjCClass, CGFloat
from toga.style import Pack


def get_bar_color(hex_color='#00CC69'):
    """Needed because apple did not provide another way.  Defaulting to the app's color."""
    hex_color = hex_color.lstrip('#')

    if len(hex_color) == 6:
        hex_color = hex_color + 'FF'

    rgba = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4, 5))

    return UIColor.colorWithRed(rgba[0], green=rgba[1], blue=rgba[2], alpha=rgba[3] / 255)


def set_bar_color(app: toga.App):
    # TODO: make it work
    rootViewController = app.main_window._impl.native.rootViewController

    appearance = rootViewController.navigationBar.standardAppearance
    appearance.backgroundColor = get_bar_color()

    rootViewController.navigationBar.standardAppearance = appearance

    print(rootViewController.navigationBar.tintColor)

    print(rootViewController.navigationBar)


UINavigationBar = ObjCClass('UINavigationBar')
UIColor = ObjCClass('UIColor')
# rootViewController = toga_iOS.window.UIWindow.objc_class
# rootViewController.navigationBar.barTintColor = get_bar_color()
# print(UINavigationBar.appearance().barTintColor)

button_style = Pack(background_color='#00CC69', color='#ffffff', padding_bottom='5')


def get_locale():
    # Retrieve the user's preferred language using NSUserDefaults
    NSUserDefaults = ObjCClass('NSUserDefaults')
    user_defaults = NSUserDefaults.standardUserDefaults
    languages = user_defaults.objectForKey_('AppleLanguages')
    # The first language in the list is the preferred language
    return str(languages[0]).split('-')[0]
