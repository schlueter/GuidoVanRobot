# -*- coding: utf-8 -*-
# Copyright (c) 2006-2007 Stas Zykiewicz <stas.zytkiewicz@gmail.com>
#
#           Editors.py
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

# Wraps the gtksourceview2

import logging
module_logger = logging.getLogger("gvr.Editors")
import os
import utils
import pygtk
pygtk.require('2.0')
import gtk
import re

# try to get the proper gtksourceview bindings
if utils.platform == 'XO':
    import gtksourceview2
    module_logger.debug("gtksourceview2 found, %s" % gtksourceview2 )
    SRCVIEW = 2
else:
    try:
        # first we try if version 2 is available
        import gtksourceview2
    except ImportError,info:
        module_logger.info("%s" % info)
        module_logger.info("No gtksourceview2, trying version 1")
        import gtksourceview
        SRCVIEW = 1
    else:
        module_logger.debug("gtksourceview2 found, %s" % gtksourceview2 )
        SRCVIEW = 2

class Editor:
    """Wraps a gtrksourceview widget and adds a few abstraction methods."""
    def __init__(self,parent,title=''):
        self.parent = parent
        self.logger = logging.getLogger("gvr.Editors.Editor")
        self.logger.debug("Using gtksourceview version %s" % SRCVIEW)
        # remove any children from previous sessions
        for child in self.parent.get_children():
            self.parent.remove(child)       
        # Look for the locale to which the syntax highlighting should be set
        # We assume the locale is available, if not there won't be any higlighting.
        try:
            loc = utils.get_locale()[:2]
        except Exception,info:
            self.logger.exception("Error in checking locale")
            loc = ''
        if loc:
            mime = 'gvr_%s' % loc
        else:
            mime = 'gvr_en'
        
        if SRCVIEW == 1:
            srctagtable = gtksourceview.SourceTagTable()
            self.srcbuffer = gtksourceview.SourceBuffer(table=srctagtable)
            man = gtksourceview.SourceLanguagesManager()
            lang = man.get_language_from_mime_type('text/x-'+mime)
            self.logger.debug("gtksourceview buffer syntax higlight set to %s" % mime)
            self.srcbuffer.set_language(lang)
            self.srcbuffer.set_highlight(True)
            self.srcview = gtksourceview.SourceView(buffer=self.srcbuffer)
            self.srcview.set_tabs_width(4)
        else:
            self.srcbuffer = gtksourceview2.Buffer()
            self.srcview = gtksourceview2.View(buffer=self.srcbuffer)
            man = gtksourceview2.LanguageManager()
            self.logger.debug("set search path to %s" % utils.GTKSOURCEVIEWPATH)
            man.set_search_path([utils.GTKSOURCEVIEWPATH])
            #man.set_search_path(["/tmp/language-specs"])
            #print dir(man)
            # Horrible hacks, gtksourceview2 on XO differs from Ubuntu :-(
            # Reminder, if XO changes their gtksourceview2 again it will probably
            # break GvRng here.
            # And of course the 767 version changes gtksourceview2 again :-(
            # You should never change existing programs and leave the original name unchanged.
            # I commented out the XO bit in case we need it when there's another change.
##            if utils.platform == 'XO':
##                langs = man.list_languages()
##                self.srcbuffer.set_highlight(True)
##                for lang in langs:
##                    for m in lang.get_mime_types():
##                        if m == 'text/x-'+mime:
##                            self.logger.debug("XO gtksourceview buffer syntax higlight set to %s" % lang)
##                            self.srcbuffer.set_language(lang)
##            else:
            langs = man.get_language_ids()
            self.srcbuffer.set_highlight_syntax(True)
            self.logger.debug("Found language files:%s" % langs)
            for id in langs:
                if id == mime:
                    self.logger.debug("gtksourceview buffer syntax higlight set to %s" % mime)
                    self.srcbuffer.set_language(man.get_language(id))
                    break
            self.srcview.set_tab_width(4)
        # some methods that are the same on version 1 and 2    
        self.tag_h = self.srcbuffer.create_tag(background='lightblue')
        self.srcbuffer.set_max_undo_levels(10)
        self.srcview.set_show_line_numbers(True)
        self.srcview.set_insert_spaces_instead_of_tabs(True)
        self.srcview.set_auto_indent(True)
        #self.srcview.set_wrap_mode(gtk.WRAP_CHAR)        
        self.parent.add(self.srcview)
        self.parent.show_all()

        self.srcbuffer.connect("delete-range",self.delete_tabs)
        # self.format results in a "Invalid text buffer iterator" warning
        self.srcbuffer.connect("insert-text", self.format)
        self.old_start_iter = None

    def get_all_text(self):
        """Return all text from the widget"""
        startiter = self.srcbuffer.get_start_iter()
        enditer = self.srcbuffer.get_end_iter()
        txt = self.srcbuffer.get_text(startiter,enditer)
        if not txt:
            return []
        if '\n' in txt:
            txt = txt.split('\n')
        else:# assuming a line without a end of line
            txt = [txt]
        return txt
        
    def set_text(self,txt):
        """Load a text in the widget"""
        #print self.__class__,'set_text',txt
        try:
            txt = ''.join(txt)
            utxt = unicode(txt)
        except Exception,info:
            print "Failed to set text in source buffer"
            print info
            return
        
        self.srcbuffer.set_text(utxt)
        
    def set_highlight(self,line):
        """Highlight the line in the editor"""
        if self.old_start_iter:
            self.srcbuffer.remove_tag(self.tag_h,self.old_start_iter,self.old_end_iter)
        end_iter = self.srcbuffer.get_iter_at_line(line)
        end_iter.forward_to_line_end()  
        start_iter = self.srcbuffer.get_iter_at_line(line)
        self.srcbuffer.apply_tag(self.tag_h,start_iter,end_iter)
        self.old_start_iter,self.old_end_iter = start_iter,end_iter
    
    def reset_highlight(self):
        self.set_highlight(0)
        
    def format(self,srcview,iter,text,leng):
        startiter = self.srcbuffer.get_start_iter()
        enditer = self.srcbuffer.get_iter_at_mark(self.srcbuffer.get_insert())
        code = self.srcbuffer.get_text(startiter,enditer)
        if len(code) > 0 and code[-1] == ":" and text == "\n":
            line = code.split('\n')[-1]
            indent = re.match("^\s*", line).group()
            self.srcbuffer.insert_interactive_at_cursor("\n"+indent + "    ", True)
        
    def delete_tabs(self,srcview,start,end):
        startiter = self.srcbuffer.get_start_iter()
        code = self.srcbuffer.get_text(startiter,end)
        cursor = self.srcbuffer.get_iter_at_mark(self.srcbuffer.get_insert())
        line = code.split('\n')[-1]
        spaces = re.match("^\s*", line).group()
        if self.srcbuffer.get_text(start,end) == " " and len(line) == len(spaces):
            if len(spaces) >= 4:
                cursor.backward_chars(4)
                self.srcbuffer.delete(cursor, end)
