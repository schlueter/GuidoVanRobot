#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2007 Stas Zykiewicz <stas.zytkiewicz@gmail.com>
#
#           gvrng.py
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License
# as published by the Free Software Foundation. A copy of this license should
# be included in the file GPL-3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.


import logging
import sys,os,__builtin__,ConfigParser
import utils
# ignore warnings as it isn't useful for the user to see them.
# At this moment, Editors.Editor.format raises a GTK warning
import warnings
warnings.simplefilter("ignore")

# commandline arguments are used for developing only
if len(sys.argv) >= 2 and sys.argv[1] == '--debug':
    CONSOLELOGLEVEL = logging.DEBUG
    FILELOGLEVEL = logging.DEBUG
else:
    CONSOLELOGLEVEL = logging.ERROR
    FILELOGLEVEL = None

PLATFORM = utils.platform

if PLATFORM != 'XO':
    fh = None
    LOGPATH = 'gvr.log'
    #create logger
    logger = logging.getLogger("gvr")
    logger.setLevel(CONSOLELOGLEVEL)
    #create console handler and set level to error
    ch = logging.StreamHandler()
    ch.setLevel(CONSOLELOGLEVEL)
    if FILELOGLEVEL:
        #create file handler and set level to debug
        fh = logging.FileHandler(LOGPATH)
        fh.setLevel(FILELOGLEVEL)
    #create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    #add formatter to ch and fh
    ch.setFormatter(formatter)
    #add ch and fh to logger
    if fh:
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    logger.addHandler(ch)
    if fh:
        logger.debug("Starting logfile: %s" % os.path.join(os.getcwd(),LOGPATH))

module_logger = logging.getLogger("gvr.gvrng")
module_logger.debug("Start logging")

if PLATFORM != 'XO':
    # This is a kludge to execute the toplevel code in utils as it is already
    # imported before the loggers are set.
    reload(utils)
    import utils

utils.setUpUnixRC()

# This stuff must be called before importing worldMap,world and guiWorld
def SetLocale(lang=None):
    global LocaleLang,LocaleMesg
    # This also sets up the global rc dict in utils.py
    rc_d = utils.parseRcFile()
    try:
        LocaleLang = rc_d['default']['lang']
    except Exception,info:
        module_logger.exception("Error reading rc dict, setting language to system")
        module_logger.error("contents of rc_d: %s" % rc_d)
        LocaleLang = 'system'
    #This will set the locale used by gvr and returns the tuple (txt,loc)
    # txt is a error message, if any else it will be an empty string.
    # loc is a string with the locale country code set for gvr, this can be
    # different from the systems locale.
    LocaleMesg = utils.set_locale(LocaleLang)

try:
    SetLocale()
except Exception,info:
    module_logger.exception("Problems setting the locale.\n switching to English\nPlease inform the GvR developers about this.")
    __builtin__.__dict__['_'] = lambda x:x

import Text
Text.set_summary(LocaleMesg[1])# needed to set summary file used to the current locale
Text.set_WBsummary(LocaleMesg[1])# idem for the worldbuilder
Text.set_Intro(LocaleMesg[1])# and the intro text

# when the frontend is not in sitepackages, as is the case for the org install
sys.path.append('gui-gtk')

import gvr_gtk # the frontend to use

import GvrModel
import GvrController

def main(handle=None,parent=None):
    module_logger.debug("main called with: %s,%s" % (handle,parent))
    try:
        # The abstraction layer on top of the gvr stuff
        model = GvrModel.GvrModel()
        # view must be the main GUI window
        if PLATFORM == 'XO':
            view = gvr_gtk.WindowXO(handle,parent)# all the gui windows runs in one window on XO
        else:
            view = gvr_gtk.Window(parent)
        # the controller must have access to the model and view
        contr = GvrController.Controller(model,view)
        # we also must give the model access to the controller
        model.set_controller(contr)
        view.set_controller(contr)
        # Now start the GUI
        contr.start_view()# args are optional
    except Exception:
        module_logger.exception("Toplevel error")
        return 1

if __name__ == "__main__":
    main()
