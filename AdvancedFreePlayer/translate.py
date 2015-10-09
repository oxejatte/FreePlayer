try:
    from Components.LanguageGOS import gosgettext as _
    #printDEBUG("LanguageGOS detected")
except:
    #printDEBUG("LanguageGOS not detected")
    from __init__ import PluginLanguageDomain , PluginLanguagePath
    from Components.Language import language
    import gettext
    from os import environ
    
    def localeInit():
        lang = language.getLanguage()[:2]
        environ["LANGUAGE"] = lang
        gettext.bindtextdomain(PluginLanguageDomain, PluginLanguagePath)

    def _(txt):
        t = gettext.dgettext(PluginLanguageDomain, txt)
        if t == txt:
                t = gettext.gettext(txt)
                print "Lack of translation for '%s'" % t
        return t

    localeInit()
    language.addCallback(localeInit)
