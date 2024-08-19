import java

platform = 'ANDROID'

def open_url(url):
    Intent = java.jclass("android.content.Intent")
    Uri = java.jclass("android.net.Uri")
    PythonActivity = java.jclass('org.beeware.android.MainActivity')

    intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
    currentActivity = PythonActivity.singletonThis
    currentActivity.startActivity(intent)


def get_locale():
    Resources = java.jclass('android.content.res.Resources')

    resources = Resources.getSystem()
    configuration = resources.getConfiguration()

    locale_list = configuration.getLocales()
    return locale_list.get(0).toString().split('_')[0]
