# coding: iso-8859-1
# Copyright (c) 2006-2010 Tampere University of Technology
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
Localization action postprocessor.

Following arguments are accepted by the postprocessor:

- file (filename, string): The name of the file that contains
  localization table in Excel-like CSV format (semicolon ; as
  delimiter).

- lang (language, string): The name of the language that should be
  used. The language identifier, such as 'fi', should appear in the
  header row of tables. If the default language is not set, the first
  language (the first column) will be used.

Localization file (maps universal names to English and Finnish):
(localization.s60v3.csv)

univ.name;en;fi
calendar_title;Calendar;Kalenteri
itemdelim;";";";"

With the above table and 'lang:fi' argument, action

kwVerifyText "§calendar_title§§itemdelim§"

is processed to

kwVerifyText "Kalenteri;"

before sending it to the test interface


*** Device-specific localization ***

The above mentioned 'file:xxx.csv', 'lang:fi', etc params define "global"
localization.

Device-specific localization is set as follows:
    'file:Device1.td:xxx.csv'
    'file:Device1.td:yyy.csv'
    'lang:Device1.td:fi'
    'file:Device2.td:xxx.csv'
    'lang:Device2.td:en'

The Device1.td is a testdata file where the devices id etc are defined.
Only one device per file. Example:
Device1(id,number): [('11123','0505050505')]

The postprocessor switches the device used for localization
when it receives the 'kw_SetTarget <id>' keyword. If no localizations are
defined for the given id, global localizations are used. If there are not even
global localizations, localization is disabled until the next kw_SetTarget.

"""

# python standard:
import re

# tema libraries:
import tema.actionpp.actionpp as actionpp
import tema.datatable.datatable as datatable
import tema.data.dataimport as dataimport


# _replace_re regexp is built so that _replace_re.findall(s) returns
# list of pairs where the first element in the pair is the string that
# should be replaced by the translated version of the second item:
# p1,p2=r.findall(s)
# new_s=s.replace(p1,translate(p2))

_replace_re=re.compile('(§([^§]+)§)')

class LocalizationException(Exception): pass

def _deviceIdFromTdFile(tdFile):
    dd = dataimport.RuntimeData().loadFromFile(file(tdFile))
    deviceNames = [name for name,data in dd.iteritems() if hasattr(data,'id')]
    if len(deviceNames) == 0:
        raise LocalizationException("No device (= something that has an id) defined in '%s'!"%(tdFile,))
    elif len(deviceNames) > 1:
        raise LocalizationException(
            "More than one device (%i) defined in '%s'. Don't know which one to use!" % (len(deviceNames),tdFile) )
    return dd[deviceNames[0]].id.val()

class _Localizer:
    def __init__(self,tdFile=None):
        """ Initializes localizer.

            If tdFile given, the deviceId is read from that,
            otherwise deviceId is None.
        """
        if tdFile is None:
            self.deviceId = None
        else:
            self.deviceId = _deviceIdFromTdFile(tdFile)
        self.tdFile = tdFile
        self._current_lang = None
        self._dt = {}
        self._files = []
        self._languages = []

    def addLocalizationFile(self,filename):
        """ Adds the contents of the given localization file to the
            localization dictionary.
        """
        self.log("Reading data from file '%s'." % filename)
        dt=datatable.DataDict(file(filename))
        self._files.append(filename)
        dt_languages=dt.header[1:]
        self.log("Found languages: %s" % ','.join(dt_languages))

        for l in dt_languages:
            if not l in self._languages: self._languages.append(l)

        # set default language if not set yet
        if self._current_lang is None:
            self.setLanguage(dt.header[1])

        self.log("%s data rows read." % len(dt))
        for univ_name in dt:
            for lang_index,lang in enumerate(dt_languages):
                key='%s\x00%s' % (lang,univ_name)
                if self._dt.has_key(key) and self._dt[key]!=dt[key]:
                    self.log(
                        ("Warning: Key '%s' in language '%s' is already "+
                         "defined to '%s'. Will not overwrite it to '%s' as "+
                         "required in file '%s'")
                        % (univ_name,lang,self._dt[key],dt[key],filename))
                else:
                    try:
                        self._dt[key]=dt[univ_name][lang_index]
                    except:
                        pass
                        self.log(
                            ("Warning: missing value for key '%s' in "+
                             "language '%s' in file '%s'")
                            % (univ_name,lang,filename))
        self.log("Localization index has now %s values." % len(self._dt))

    def setLanguage(self,lang):
        self._current_lang = lang
        self.log("The language of device '%s' changed to '%s'" %
                 (self.deviceId,lang))

    def process(self,actionname):
        """Returns the localized action.
        """
        newactionname=actionname
        for whole_str,univ_name in _replace_re.findall(actionname):
            key='%s\x00%s' % (self._current_lang,univ_name)
            if not self._dt.has_key(key):
                self.log("Cannot localize key '%s' to language '%s' in %s" %
                         (univ_name,self._current_lang,actionname))
            else:
                newactionname=newactionname.replace(whole_str,self._dt[key],1)
        if actionname!=newactionname:
            self.log("Localized: '%s' to '%s'" % (actionname,newactionname))
        return newactionname


class LocalizationPP(actionpp.ActionPP):

    def __init__(self):

        self._localizersById = {}
        self._localizersByTdFile = {}
        self._currentLocalizer = None
        self._globalLocalizer = None

        actionpp.ActionPP.__init__(self)

    def setParameter(self,parametername,parametervalue):
        if parametername=="file":
            loc,langFile = self._getParamTargetAndValue(parametervalue)
            loc.addLocalizationFile(langFile)

        elif parametername=="lang":
            loc,lang = self._getParamTargetAndValue(parametervalue)
            loc.setLanguage(lang)
        else:
            print __doc__
            raise Exception("Invalid parameter '%s' for localspp." % parametername)

    def setLanguage(self,lang):
        """Sets the global language."""
        if not self._globalLocalizer:
            self._createGlobalLocalizer()
        self._globalLocalizer.setLanguage(lang)

    def setLanguageOfDevice(self,lang,deviceId):
        """Sets the language of device with the given deviceId."""
        if deviceId in self._localizersBy:
            self._localizersById[deviceId].setLanguage(lang)
        else:
            self.log("No such device id: '%s')" % (deviceId,))


    def process(self,actionname):
        """Returns the localized version of the actionname.

        Using localizations of the currently active device,
        or global localizations if none active.

        The active device is changed when this method receives 'kw_SetTarget'
        keyword.
        """
        if actionname.startswith('kw_SetTarget '):
            kwst,deviceId = actionname.split()
            if deviceId in self._localizersById:
                self._currentLocalizer = self._localizersById[deviceId]
                self.log("Changed device. New device id: '%s', tdFile: '%s'."
                     % (self._currentLocalizer.deviceId,
                        self._currentLocalizer.tdFile,))
            else:
                self.log("No localizations defined for device id '%s'."
                         % deviceId)
                self._currentLocalizer = None
                if self._globalLocalizer:
                    self.log("Using global localizations.")
                else:
                    self.log("No global localizations defined."+
                             "Localization disabled.")
            return actionname

        if self._currentLocalizer:
            return self._currentLocalizer.process(actionname)
        elif self._globalLocalizer:
            return self._globalLocalizer.process(actionname)
        else:
            return actionname

    def _getParamTargetAndValue(self,parametervalue):
        """ If paramval is 'XXX.td:YYY' returns (the XXX.td localizer, 'YYY')
            If paramval is 'YYY' returns (the global localizer, 'YYY')
            The localizer is created if it doesn't already exist.
        """
        params = parametervalue.split(':',1)
        if len(params)==1:
            if not self._globalLocalizer:
                self._createGlobalLocalizer()
            return self._globalLocalizer, params[0]
        else:
            tdFile,paramval = params
            if tdFile in self._localizersByTdFile:
                return self._localizersByTdFile[tdFile], params[1]
            else:
                loc = self._createLocalizer(tdFile)
                return loc, params[1]

    def _createLocalizer(self,tdFile):
        loc = _Localizer(tdFile)
        loc.log = self.log
        self._localizersById[loc.deviceId] = loc
        self._localizersByTdFile[loc.tdFile] = loc
        return loc

    def _createGlobalLocalizer(self):
        self._globalLocalizer = _Localizer()
        self._globalLocalizer.log = self.log
        return self._globalLocalizer


ActionPP=LocalizationPP
