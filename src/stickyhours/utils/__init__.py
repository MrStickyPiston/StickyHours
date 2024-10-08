import toga.platform

print(f"Initializing on platform: {toga.platform.get_current_platform()}")

from .default import *

if toga.platform.get_current_platform() == 'android':
    from .android import *
elif toga.platform.get_current_platform() == 'iOS':
    from .ios import *
elif toga.platform.get_current_platform() == 'windows':
    from .windows import *
elif toga.platform.get_current_platform() == "macOS":
    from .macos import *