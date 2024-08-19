from rubicon.objc import ObjCClass
from toga.style import Pack

platform = "IOS"

button_style = Pack(background_color='#00CC69', color='#ffffff', padding_bottom='5')


def get_locale():
    # Retrieve the user's preferred language using NSUserDefaults
    NSUserDefaults = ObjCClass('NSUserDefaults')
    user_defaults = NSUserDefaults.standardUserDefaults
    languages = user_defaults.objectForKey_('AppleLanguages')
    # The first language in the list is the preferred language
    return str(languages[0]).split('-')[0]
