import toga.platform

from .default import *

if toga.platform.get_current_platform() == 'android':
    from .android import *
