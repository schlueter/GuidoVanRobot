# -*- coding: utf-8 -*-

# Copyright (c) 2006 Stas Zykiewicz <stas.zytkiewicz@gmail.com>
#
#           Win_Editors.py
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

# Provides a textview widget which is packed inside the glade generated 
# TextEditorWin from gvr_gtk.py
# Only used on Windows, on GNU/Linux we use a wrapped gtksourceview widget.
# Things missing in this editor:
# Syntax highlighting
# folding and indentation markers


E_DEBUG = 0
import os,sys
import utils
import pygtk

#this is needed for py2exe
if sys.platform == 'win32':
    pass
else:
    #not win32, ensure version 2.0 of pygtk is imported
    pygtk.require('2.0')

import gtk

class Editor:
    """Wraps a textview widget and adds a few abstraction methods."""
    def __init__(self,parent,title=''):
        self.parent = parent
        
        self.frame = gtk.Frame()
        
        self.txttagtable = gtk.TextTagTable()
        self.txtbuffer = gtk.TextBuffer(table=self.txttagtable)
        
        self.tag_h = self.txtbuffer.create_tag(background='lightblue')
        
        self.txtview = gtk.TextView(buffer=self.txtbuffer)
        self.txtview.set_border_window_size(gtk.TEXT_WINDOW_LEFT, 20)                
        self.txtview.connect("expose_event", self.line_numbers_expose)
        
        self.parent.add(self.txtview)
        self.parent.show_all()
        
        self.old_start_iter = None

    def get_all_text(self):
        """Return all text from the widget"""
        startiter = self.txtbuffer.get_start_iter()
        enditer = self.txtbuffer.get_end_iter()
        txt = self.txtbuffer.get_text(startiter,enditer)
        if not txt:
            return []
        if '\n' in txt:
            txt = txt.split('\n')
        else:# assuming a line without a end of line
            txt = [txt]
        return txt
        
    def set_text(self,txt):
        """Load a text in the widget"""
        if E_DEBUG: print self.__class__,'set_text',txt
        try:
            txt = ''.join(txt)
            utxt = unicode(txt)
        except Exception,info:
            print "Failed to set text in source buffer"
            print info
            return
        self.txtbuffer.set_text(utxt.rstrip('\n'))
        
    def set_highlight(self,line):
        """Highlight the line in the editor"""
        if self.old_start_iter:
            self.txtbuffer.remove_tag(self.tag_h,self.old_start_iter,self.old_end_iter)
        end_iter = self.txtbuffer.get_iter_at_line(line)
        end_iter.forward_to_line_end()  
        start_iter = self.txtbuffer.get_iter_at_line(line)
        self.txtbuffer.apply_tag(self.tag_h,start_iter,end_iter)
        self.old_start_iter,self.old_end_iter = start_iter,end_iter
    
    def reset_highlight(self):
        self.set_highlight(1)
    
    ##### taken from pygtk tutorial example ######################
    def line_numbers_expose(self, widget, event, user_data=None):
        text_view = widget
  
        # See if this expose is on the line numbers window
        left_win = text_view.get_window(gtk.TEXT_WINDOW_LEFT)
        
        if event.window == left_win:
            type = gtk.TEXT_WINDOW_LEFT
            target = left_win
        else:
            return False
        
        first_y = event.area.y
        last_y = first_y + event.area.height

        x, first_y = text_view.window_to_buffer_coords(type, 0, first_y)
        x, last_y = text_view.window_to_buffer_coords(type, 0, last_y)

        numbers = []
        pixels = []
        count = self.get_lines(first_y, last_y, pixels, numbers)
        # Draw fully internationalized numbers!
        layout = widget.create_pango_layout("")
  
        for i in range(count):
            x, pos = text_view.buffer_to_window_coords(type, 0, pixels[i])
            numbers[i] = numbers[i] + 1
            str = "%d" % numbers[i] 
            layout.set_text(str)
            widget.style.paint_layout(target, widget.state, False,
                                      None, widget, None, 2, pos + 2, layout)

        # don't stop emission, need to draw children
        return False
        
    def get_lines(self, first_y, last_y, buffer_coords, numbers):
        text_view = self.txtview
        # Get iter at first y
        iter, top = text_view.get_line_at_y(first_y)

        # For each iter, get its location and add it to the arrays.
        # Stop when we pass last_y
        count = 0
        size = 0

        while not iter.is_end():
            y, height = text_view.get_line_yrange(iter)
            buffer_coords.append(y)
            line_num = iter.get_line()
            numbers.append(line_num)
            count += 1
            if (y + height) >= last_y:
                break
            iter.forward_line()

        return count
        
        
