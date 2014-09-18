# -*- coding: utf-8 -*-

# Copyright (c) 2007 Stas Zykiewicz <stas.zytkiewicz@gmail.com>
#
#           utils.py
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

# set this for XO or linux

#platform = 'XO'
platform = 'linux'

import logging, imp
module_logger = logging.getLogger("gvr.utils")
module_logger.debug("platform is %s" % platform)

import os,sys,traceback,gettext,locale,__builtin__,shutil,types,ConfigParser,atexit

def get_rootdir():
    """Returns the CWD of GvR"""
    if platform == 'XO':
        return os.getcwd()
    else:
        if (hasattr(sys, "frozen") or # new py2exe
            hasattr(sys, "importers") or # old py2exe
            imp.is_frozen("__main__")): # tools/freeze
            print os.path.dirname(sys.path[0])
            print os.path.abspath(sys.path[0])
            print sys.path[0]
            return os.path.dirname(sys.path[0])
        else:
            return sys.path[0]

if platform == 'XO':
    RCFILE = os.path.join(os.environ['SUGAR_ACTIVITY_ROOT'],'data','gvrngrc')
    PROGRAMSDIR = os.path.join(os.environ['SUGAR_ACTIVITY_ROOT'],'data','GvR')
    GTKSOURCEVIEWPATH = os.path.join(os.environ['SUGAR_ACTIVITY_ROOT'],'data','.gnome2/gtksourceview-1.0/language-specs')
else:
    RCFILE = os.path.expanduser('~/.gvrngrc')
    PROGRAMSDIR = os.path.join(os.path.expanduser('~'),'GvR')
    GTKSOURCEVIEWPATH = os.path.join(os.path.expanduser('~'),'.gnome2/gtksourceview-1.0/language-specs')
# Basic world description used as a fallback in case of an exception when loading
# a world file from the editor window.
NULL_WORLD = 'Robot 1 1 N 0'
# will hold the locale set by set_locale()
LANG_TRANS = ''
LANG = ''
# will be set by calling parseRcFile()
RCDICT = {}

# path to the frontend(s) etc
# Intended to make packaging easier 
FRONTENDDIR = os.path.join(get_rootdir(),'gui-gtk')
PIXMAPSDIR = os.path.join(get_rootdir(),'gui-gtk','pixmaps')
LOCALEDIR = os.path.join(get_rootdir(),'locale')

module_logger.debug("Constant paths:")
module_logger.debug("RCFILE %s" % RCFILE)
module_logger.debug("LOCALEDIR %s" % LOCALEDIR)
module_logger.debug("FRONTENDDIR %s" % FRONTENDDIR)
module_logger.debug("PIXMAPSDIR %s" % PIXMAPSDIR)
module_logger.debug("PROGRAMSDIR %s" % PROGRAMSDIR)
module_logger.debug("GTKSOURCEVIEWPATH %s" % GTKSOURCEVIEWPATH)

gvrrcHeader = """
# Configuration file for GvRng, Guido van Robot Next Generation.
# You can set the language GvRng will use.
#

# Possible languages are:
# system > Use the systems default language, this defaults to English when the
#          systems language is not supported.
#
# The language is specified by given the locale for that language, so for
# Dutch one should do: lang=nl_NL@euro
# You can only give valid locales. A valid locale is a locmodule_logger.debug("Start setUpUnixRC")ale you have
# configured properly on your system.
# For example; you do this, lang=nl_NL@euro, but your system only has a locale
# nl_NL. In this case you will see a error message (stderr) and the GUI would
# be mostly be in English.  
#
# These are examples of locales, the languages are the ones that are currently
# supported by gvrng
#
# nl_NL@euro > Dutch
# ca_Es@euro > Catalan
# fr_FR@euro > French
# ro_RO.utf8 > Romanian
# nb_NO > Norwegian bokmal
# de_DE@euro > German
# es_ES@euro > Spanish

"""

GVRREDIRECT = 1# redirect stderr and stdout to files (see out.py)
# This redirecting of streams is only used on the non-linux platforms
# to capture messages from the app when running in a console-less way.
# (mainly .exe)
if os.name == 'nt' and GVRREDIRECT:
    try:
        import out
    except ImportError,info:
        print >> sys.stderr,info
    else:
        print >> sys.stderr,"Redirect sys.stderr"
        print "Redirect sys.stdout"
        
def get_locale():
    """Get the systems locale.
    This can be different from the locale used by gvr.(see set_locale())"""
    if LANG:
        # we use the language set by set_locale
        return LANG
    try:
        lang = ''
        # FIX locale.py LANGUAGE parsing bug, the fix was added on the
        # upstream CVS on the 1.28.4.2 revision of 'locale.py', It
        # should be included on Python 2.4.2.
        if os.environ.has_key('LANGUAGE'):
            lang = os.environ['LANGUAGE'].split(':')[0]
        # This makes sure that we never return a value of None.
        # This is a fix for systems that set LANGUAGE to ''.
        if lang == '':
            lang = locale.getdefaultlocale()[0]
    except Exception,info:
        if 'en' in lang:
            pass
        else:
            module_logger.exception("Error in setting the locale, switching to English")
            lang = 'en'
    return lang
    
def set_locale(lang=None):
    """Set the locale to be used by gvr.
    It will first check th rc file and then the systems locale.
    It uses English (en) as the fallback locale.
    It will also set a global constant holding the locale used called LANG_TRANS."""
    module_logger.debug("set_locale called with %s" % lang)
    global LANG_TRANS,LANG,LOC
    lang_trans = 'en'
    txt = ""
    try:
        # "system" is/can be used to signal that the sysytem locale should be used
        # from a config file, see also gvrrc 
        if not lang or lang == '' or lang == 'system':
            lang = get_locale()
        if lang == 'en': 
            __builtin__.__dict__['_'] = lambda x:x
            return ("","en")
        languages = [ lang ]
        if os.environ.has_key('LANGUAGE'):
            languages += os.environ['LANGUAGE'].split(':')
        module_logger.debug("languages found are %s" % languages)
        lang_trans = gettext.translation('gvrng',\
                                     localedir=LOCALEDIR,\
                                     languages=languages)
        __builtin__.__dict__['_'] = lang_trans.ugettext
        # seems this is the only way to get glade to use the locale setting
        module_logger.debug("Set env var LANGUAGE to %s" % lang)
        os.environ['LANGUAGE'] = lang
    except Exception,info:
        txt=""
        if lang and lang.split('@')[0].split('.')[0].split('_')[0] != 'en':
            module_logger.exception("Cannot set language to '%s' \n switching to English" % lang)
        __builtin__.__dict__['_'] = lambda x:x
        return (txt,"en")
    LANG_TRANS = lang_trans
    LANG = lang
    return ("",lang)

def trace_error(file=sys.stderr):
    """  Print a stack trace useful for debugging"""
    print >> file, '*'*60
    info = sys.exc_info()
    traceback.print_exception(info[0],info[1],info[2],file)
    print >> file,' Please send a bug report with this stuff to,\n stas.zytkiewicz@gmail.com'
    print >> file,'*'*60

def isOsX():
    if os.name == 'posix' and os.uname()[0] == 'Darwin':
        return 1
    return 0

def setUpUnixRC():
    module_logger.debug("Start setUpUnixRC")
    if not os.path.exists(RCFILE):
        src = os.path.join(get_rootdir(),'gvrngrc')
        try:
            shutil.copy(src,RCFILE)
        except Exception,info:
            module_logger.exception("Error in setting user files")
    if not os.path.exists(PROGRAMSDIR):
        shutil.copytree(os.path.join(get_rootdir(),'gvr_progs'),PROGRAMSDIR)
        
    # gtksourceview2 is now available on the XO, hooray :-)
    dest = GTKSOURCEVIEWPATH
    if not os.path.exists(dest):
        os.makedirs(dest)
    if not os.path.exists(os.path.join(dest,'gvr_en.lang')):
        # we assume that the other language files also don't exists
        import glob
        src = os.path.join(get_rootdir(),'po')
        files = glob.glob(src+'/*.lang')
        module_logger.debug("found language files: %s" % files)
        for file in files:
            langdest = os.path.join(dest,os.path.basename(file))
            module_logger.debug("copy %s to %s" % (file,langdest))
            shutil.copy(file,langdest)
       
def load_file(path):
    """Loads a file and returns the contents as a list of strings.
    Returns a empty list on faillure."""
    try:
        f = open(path,'r')
        txt = f.readlines()
        f.close()
    except IOError:
        module_logger.exception("Failed to load file")
        return []
    else:
        return txt
        
def save_file(path,content):
    """Saves the content to the given path.
    Return None on success and en error text on faillure.
    @content must be a list of strings."""
    try:
        f = open(path,'w')
        f.write('\n'.join(content))
        f.close()
    except Exception,info:
        trace_error()
        return (_("Failed to save the file.\n")+str(info))
    else:
        return None
    
def setRcEntry(option,value):
    try:
        cp = ConfigParser.ConfigParser()
        cp.read(RCFILE)
        cp.set("default", option,value)
        rcfile = open(RCFILE,'w')
        rcfile.write(gvrrcHeader)
        cp.write(rcfile)
        rcfile.close()
    except Exception,info:
        txt = "Failed to write the configuration to disk.\n" 
        print >> sys.stderr,txt,info
        return txt
    else:
        txt = _("Written the new configuration to disk\nYou have to restart GvRng to see the effect")
        print txt  
        return txt
    
def parseRcFile():
    """parse and return rcfile entries in a dict"""
    global RCDICT
    rc_d,rc_p = {},{}
    try:
        cp = ConfigParser.SafeConfigParser()
        cp.read(RCFILE)
        for k,v in cp.items("default"):
            rc_d[k] = v
        for k,v in cp.items("printer_options"):
            rc_p[k] = v
    except Exception,info:
        print >> sys.stderr,info,"Setting language and printer to defaults." 
        print "========================================================="
        print "The configuration file used by GnRng is changed."
        print "You should remove %s and restart GvRng." % os.path.expanduser('~/.gvrngrc')
        print "A new configuration will be installed in your home directory"
        print "========================================================="
        rc_d['lang'] = 'system'
        rc_d['printer'] = 'lp'
        rc_d['intro'] = 'yes'
    # we also set them as globals. objects can do utils.PRINTERCMD to get them.
    RCDICT = {'default':rc_d,'printer_options':rc_p}
    return RCDICT    
        
def send_to_printer(path):
    """This will send file @path to a printer by using the command and options
    from the gvrngrc file."""
    print 'RCDICT',RCDICT
    opts = []
    try:
        cmd = RCDICT['default']['printercmd']
        if 'lp' in cmd:
            for k,v in RCDICT['printer_options'].items():
                opts.append(' -o %s=%s' % (k,v))
            cmd = cmd + ''.join(opts)+' '+path
    except Exception,info:
        print info
        return
    module_logger.debug("printer cmd %s" % cmd)   
    try:
        os.system(cmd)
    except Exception,info:
        print info

