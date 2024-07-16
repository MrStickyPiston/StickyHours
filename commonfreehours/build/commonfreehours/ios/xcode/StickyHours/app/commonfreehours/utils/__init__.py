import toga.platform

print(f"Initializing on platform: {toga.platform.get_current_platform()}")

from .default import *

if toga.platform.get_current_platform() == 'android':
    from .android import *
