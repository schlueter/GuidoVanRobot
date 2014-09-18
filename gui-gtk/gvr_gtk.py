#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2007 Stas Zykiewicz <stas.zytkiewicz@gmail.com>
#
#           gvr_gtk.py
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

# Reminder:
# "widgets in classes derivated from SimpleGladeApp is easy and intuitive.
# So, a widget created with glade you named 'bogus_widget' will be used in
# your code as 'self.bogus_widget'."

import version
app_name = "gvrng"# used to set gettext
app_version = version.VERSION

import sys,os,logging
import utils,Text

glade_dir = utils.FRONTENDDIR
locale_dir = utils.LOCALEDIR

from SimpleGladeApp import SimpleGladeApp
from SimpleGladeApp import bindtextdomain

import pygtk
# ensure version >= 2.0 of pygtk is imported
pygtk.require('2.0')

import gtk

# tell gtk we gonna use threads 
import gobject
gobject.threads_init()

module_logger = logging.getLogger("gvr.gvr_gtk")

PLATFORM = utils.platform
if PLATFORM == 'XO':
    from sugar.activity import activity as sgactivity  
else:
    import fake_sugar_activity as sgactivity
module_logger.debug("Using sugar activity module: %s" % sgactivity)    
    
if sys.platform == 'win32':
    import Win_Editors as Editors
else:
    import Editors
import Widgets

bindtextdomain(app_name, utils.get_locale(),locale_dir)

class Globals(super):
    speed = _('Medium')

class Window(SimpleGladeApp):
    def __init__(self, parent=None, path="gvr_gtk.glade", root="window_main", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)
        
        self.logger = logging.getLogger("gvr.gvr_gtk.Window")
        if PLATFORM != 'XO':
            #self.parentGUI = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.parentGUI = self.window_main
            self.windowtitle = "GvRng"
            self.parentGUI.set_title(self.windowtitle)
            file = os.path.join(os.getcwd(),'gui-gtk','pixmaps','gvrIcon.bmp')
            try:
                self.parentGUI.set_icon_from_file(file)
            except gobject.GError:
                self.logger.exception("Can't load window icon")
            #self.parentGUI.set_size_request(800,600)
            self.parentGUI.connect('delete_event',self.stop)
            
            # We setup key event callback here as WBCanvas can't recieve them ?? XXX
            self.parentGUI.add_events( gtk.gdk.KEY_PRESS_MASK )
            
            # delete lessons tab as we don't have an embedded browser
            self.eventboxlessons.destroy()
            self.lessons.destroy()
        
        # set the localized language summary in the language reference tab
        # first line is also used as the title
        txt = Text.OnRefText
        #title = txt.split('\n')[0]
        buffer = gtk.TextBuffer(table=None)
        try:
            txt = ''.join(txt)
            utxt = unicode(txt)
        except Exception,info:
            self.logger.exception("Failed to set reference text in source buffer")
            return
        buffer.set_text(utxt)
        self.textview_languagereference.set_buffer(buffer)
        self.textview_languagereference.show_all()
        # and set the intro text
        txt = Text.OnIntroText
        buffer = gtk.TextBuffer(table=None)
        try:
            txt = ''.join(txt)
            utxt = unicode(txt)
        except Exception,info:
            self.logger.exception("Failed to set intro text in source buffer")
            return
        buffer.set_text(utxt)
        self.textview_intro.set_buffer(buffer)
        self.textview_intro.show_all()
        # check if we should show the intro text on startup.
        try:
            if utils.RCDICT['default']['intro'].lower() == 'yes':
                self.notebook1.set_current_page(-1)
                utils.setRcEntry('intro','no')
        except KeyError:
            # versions < 2.9 don't have 'intro', but those users already know gvr :-)
            pass
         
        # only needed for debugging
        #self.parentGUI.connect('size-allocate', self._on_size_allocate)
        
    # Only used for debugging    
##    def _on_size_allocate(self, widget, allocation):
##        self.width = allocation.width
##        self.height = allocation.height
##        self.logger.debug("parentGUI x,y: %s" % (self.width,self.height))
##        return True    
        
    
    def new(self):
        # called by SimpleGladeApp
        self.statusbar = Widgets.StatusBar(self.statusbar7)
        self._setup_canvas()
        # these calls will add the editors to the GUI
        self.new_world_editor()
        self.new_program_editor()
        self._set_sensitive_button('all',True)
        self.timerinterval = 150
    
    def new_world_editor(self):
        self.world_editor = WorldTextEditorWin(parent=self)
    def new_program_editor(self):
        self.program_editor = CodeTextEditorWin(parent=self)
    
    def _setup_canvas(self):
        # setup the canvas
        self._canvas = Widgets.Canvas()
        self.align = gtk.Alignment()
        self.viewport = gtk.Viewport()
        self.scrolledwindow8.add(self.viewport)
        self.viewport.add(self._canvas)
        self.scrolledwindow8.show_all()
        self._set_sensitive_button('all',False)
        self.WB_ACTIVATED = False
    def _set_sensitive_button(self,button,value):
        """used to 'grey out' buttons.
        When the @button is 'all', all the buttons are handled.
        We also clear the statusbar if the buttons are disabled."""
        if button == 'all':
            for b in (self.button_abort,self.button_execute,
                        self.button_reload,self.button_step):
                b.set_sensitive(value)
        else:
            but = {'abort':self.button_abort,
                'reload':self.button_reload,
                'execute':self.button_execute,
                'step':self.button_step}[button]
            but.set_sensitive(value)
        if button == 'all' or button in ('reload','step') and value == False:
            self.statusbar.clear()
    def _worldeditor_observer_callback(self):
        self.world_editor = None
    def _programeditor_observer_callback(self):
        self.program_editor = None
        
    ## These are the callbacks mandatory for the controller
    def start(self,*args):
        """This will start the GUI."""
        self.logger.debug("start called with args: %s" % args)
        # there are only args when gvr is started by gvrng.py (non-XO systems)
        if args[0] and args[1]:
            wfile, pfile = args[0], args[1]
            self.world_editor.on_new1_activate(file=wfile)
            self.program_editor.on_new1_activate(file=pfile)
        # Sugar runs the gtk loop on XO
        if PLATFORM != 'XO':
            self.parentGUI.show()
            self.run()
         
    def get_timer(self):
        """The controller will call this and expect to get a timer object.
         The timer must provide the following methods:
         start, stop, set_func and set_interval
         see the timer docstrings for more info"""
        return Widgets.Timer()
    
    def get_timer_interval(self):
        return self.timerinterval
    
    def stop(self,*args):
        """Stops the gui, when running in non-XO"""
        gtk.main_quit()
    
    def set_controller(self,contr):
        self.logger.debug("controller set in %s" % self)
        self.controller = contr
    
    def worldwin_gettext(self):
        if self.world_editor:
            wcode = self.world_editor.get_all_text()
            if wcode:
                return wcode
        self.show_warning(_("You don't have a world file loaded."))
    
    def codewin_gettext(self):
        if self.program_editor:
            wcode = self.program_editor.get_all_text()
            if wcode:
                return wcode
        self.show_warning(_("You don't have a program file loaded."))
    
    def highlight_line_code_editor(self,line):
        """ Controller calls this with the current line of code that's
        been executed after the execute button is pressed."""
        try:
            self.program_editor.editor.set_highlight(line)
        except Exception,info:
            print info
    
    def show_warning(self,txt):
        Widgets.WarningDialog(txt=txt)
    
    def show_error(self,txt):
        Widgets.ErrorDialog(txt=txt)
    
    def show_info(self,txt):
        Widgets.InfoDialog(txt=txt)
    
    def update_world(self,obj):
        """Called by the controller when the world is changed."""
        # canvas is the drawable from Widgets.Canvas
        self._canvas.draw_world(obj)
        pos = self.controller.get_robot_position()
        self.logger.debug("received from controller robot position %s,%s" % pos)
        self.statusbar.update_robotposition(pos)
        beep = self.controller.get_robot_beepers()
        self.logger.debug("received from controller number of beepers %s" % beep)
        self.statusbar.update_robotbeepers(beep)
    
    def update_robot_world(self,obj,oldcoords=None):
        """Called by the controller when the robots position is changed."""
        self._canvas.draw_robot(obj,oldcoords)
        pos = self.controller.get_robot_position()
        #self.logger.debug("received from controller robot position %s,%s" % pos)
        self.statusbar.update_robotposition(pos)
    
    def update_beepers_world(self,obj):
        """Called by the controller when the beepers states are changed."""
        self._canvas.draw_beepers(obj)
        beep = self.controller.get_robot_beepers()
        #self.logger.debug("received from controller number of beepers %s" % beep)
        self.statusbar.update_robotbeepers(beep)
    ### end of mcv methods
    
    def on_MainWin_delete_event(self, widget, *args):
        self.on_quit1_activate(widget)
        return True # Don't send the signal further
    
    def on_open_worldbuilder1_activate(self, widget, *args):
        self.logger.debug("worldbuilder_activate")
        self.WB_ACTIVATED = True
        if PLATFORM != 'XO':
            self.windowtitle = self.parentGUI.get_title()
            self.parentGUI.set_title(_("GvR - Worldbuilder"))
        
        # first we disable all the buttons.
        self._set_sensitive_button('all',False)
        # We (re)activate the buttons reload and abort as they are used by
        # the WB. The reload button reacts by reloading the canvas, just as
        # in a normal session. For the abort button we set a flag which is checked
        # by the on_button_abort callback to act as a WB 'quit' button.
        self._set_sensitive_button('reload',True)
        self._set_sensitive_button('abort',True)
        # As we might not have a world when we start WB we start with a empty world
        # with Guido in the bottom left corner facing east, no beepers.
        # We start with a localized statement.
        wcode = ["%s 1 1 %s 0" % (_("robot"),_("E"))]
        if self.world_editor.get_all_text():
            # if there's an open world editor we use it's contents
            wcode = self.world_editor.get_all_text()
        else:
            self.world_editor.editor.set_text(wcode)
        # When the world_editor is destroyed it will call the observer.
        # By doing this it will simulate a abort button event.
        # TODO: check this whole destroy stuff, do we use it ?
        self.world_editor.register_observer(self.on_button_abort)
        # store the canvas so we can restore it later
        # It's also to add a reference to it to make sure the Python GC don't
        # free it from memory
        # TODO: Do we need to keep it ???
        self.oldcanvas = self._canvas
        self.viewport.remove(self._canvas)
        # setup the wb canvas
        self._canvas = Widgets.WBCanvas(parent=self,wcode=wcode)
        self.viewport.add(self._canvas)
        self.scrolledwindow8.show_all()
        # reload an empty world into the canvas which is now the WB canvas.
        # The wb canvas 'is a' normal canvas so all the methods and logic we
        # use in a normal grv session apply also in a WB session. 
        self.on_button_reload()
        #self.on_gvr_worldbuilder1_activate()
        self.statusbar.set_text(_("Running Worldbuilder"))
    
    def on_quit1_activate(self, widget, *args):
        self.logger.debug("on_quit1_activate called")
        try:
            self.program_editor.on_quit2_activate()
        except Exception, info:
            pass
            #print info
        try:
            self.world_editor.on_quit2_activate()
        except Exception,info:
            pass
            #print info
        dlg = QuitDialog()
        dlg.QuitDialog.show()
    
    def on_set_speed1_activate(self, widget, *args):
        dlg = SetSpeedDialog()
        response = dlg.SetSpeedDialog.run()
        if response == gtk.RESPONSE_OK:
            self.timerinterval = dlg.get_choice()
        dlg.SetSpeedDialog.destroy()
    
    def on_gvr_lessons1_activate(self, widget, *args):
        """Display the GvR lessons in the default browser.
        This only works if the gvr lessons package version 0.2 is installed."""
        import webbrowser
        file = os.path.join(utils.get_rootdir(),'docs','lessons',utils.get_locale()[:2],'html','index.html')
        self.logger.debug("Looking for the lessons in %s" % file)
        if not os.path.exists(file) and utils.get_locale()[:2] != 'en':
            file = os.path.join(utils.get_rootdir(),'docs','lessons','en','html','index.html')
            self.logger.debug("Looking for the lessons in %s" % file)
        if os.path.exists(file):
            try:
                webbrowser.open(file,new=0)
            except webbrowser.Error,info:
                txt = str(info)+ '\n'+ "Be sure to set your env. variable 'BROWSER' to your preffered browser."
                self.show_warning(txt)
        else: 
            self.show_warning(_("Can't find the lessons.\nMake sure you have installed the GvR-Lessons package.\nCheck the GvR website for the lessons package.\nhttp://gvr.sf.net"))
                               
##    def on_set_language1_activate(self, widget, *args):                     
##        dlg = SetLanguageDialog()
##        response = dlg.SetLanguageDialog.run()
##        if response == gtk.RESPONSE_OK:
##            languagechoice = dlg.get_choice()
##        dlg.SetLanguageDialog.destroy()
##        #print "languagechoice",languagechoice
##        utils.setRcEntry('lang',languagechoice)
    
##    def on_gvr_reference1_activate(self, widget, *args):
##        dlg = SummaryDialog()
##        dlg.set_text(Text.OnRefText)
    
    def on_gvr_worldbuilder1_activate(self,*args):
        dlg = SummaryDialog()
        dlg.set_text(Text.OnWBText)

    def on_about1_activate(self, widget, *args):
        #testing
        #self.button_abort.set_sensitive(False)
        dlg = AboutDialog()
    
    def on_button_reload(self, *args):
        wcode = self.worldwin_gettext()
        if wcode:
            self.controller.on_button_reload(wcode)
        self.program_editor.reset_highlight()
        self._canvas._reset_offset()
        # notify wbuilder that possibly the world editor code is changed.
        if self.WB_ACTIVATED and wcode:
            self._canvas.reload_button_activated(wcode)
        return True

    def on_button_step(self, widget, *args):
        self.controller.on_button_step()
        return True
    
    def on_button_execute(self, widget, *args):
        self.controller.on_button_execute()
        return True
    
    def on_button_abort(self, widget=None, *args):
        if self.WB_ACTIVATED:
            # we act now as a 'quit button for the WB
            # canvas is now a WBCanvas object
            # Reset everything for the 'normal' canvas
            if PLATFORM != 'XO':
                self.parentGUI.set_title(self.windowtitle)
            self._set_sensitive_button('all',False)
            self.scrolledwindow8.remove(self.viewport)
            # put back the gvr world canvas
            self._setup_canvas()
            if not widget:
                # If widget is None we are called by the WB in a situation
                # the user has destroyed the worldeditor.
                self.world_editor = None 
            if self.world_editor:
                self._set_sensitive_button('reload',True)
                self.on_button_reload()
            if self.program_editor:
                for b in ('execute','step','abort'):
                    self._set_sensitive_button(b,True)
        else:
            self.controller.on_button_abort()
    
    def on_statusbar1_text_popped(self, widget, *args):
        pass
    
    def on_statusbar1_text_pushed(self, widget, *args):
        pass
        
class WindowXO(Window):
    def __init__(self, handle,parent=None, path="gvr_gtk.glade", root="window_main", domain=app_name, **kwargs):
        Window.__init__(self,parent=parent, path=path, root=root, domain=domain)
        self._parent = parent
        self.logger = logging.getLogger("gvr.gvr_gtk.WindowXO")
        
        # Get and set the sugar toolbar
        toolbox = sgactivity.ActivityToolbox(self._parent)
        self._parent.set_toolbox(toolbox)
        toolbox.show()

        # then we remove the main frame from parent
        self._frame = self.frame5
        self.window_main.remove(self._frame)
        # set as main window below the toolbox
        self._parent.set_canvas(self._frame)
        self._frame.show()
        
        # remove seperator and 'quit' menu items as we have the sugar toolbox 
        self.separatormenuitem14.destroy()
        self.imagemenuitem49.destroy()
        
        # Embed webview as the lessons display 
        self.logger.debug("import webview")
        import hulahop
        from sugar import env
        hulahop.startup(os.path.join(env.get_profile_path(), 'gecko'))
        from hulahop.webview import WebView
        self.WV = WebView()
        
        file = os.path.join(utils.get_rootdir(),'docs','lessons',utils.get_locale()[:2],'html','index.html')
        self.logger.debug("Looking for the lessons in %s" % file)
        if not os.path.exists(file):
            self.logger.debug("%s not found, loading default English lessons" % file)
            file = os.path.join(utils.get_rootdir(),'docs','lessons','en','html','index.html')
        self.WV.load_uri('file:///%s' % file)
        self.WV.show()
        vbox = gtk.VBox(False,4)
        vbox.pack_start(Widgets.WebToolbar(self.WV),False,False,2)
        vbox.pack_start(self.WV,True,True,2)
        vbox.show_all()
        self.eventboxlessons.add(vbox)

        
        
class QuitDialog(SimpleGladeApp):
    def __init__(self, path="gvr_gtk.glade", root="QuitDialog", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)

    def new(self):
        #print "A new QuitDialog has been created"
        pass
    
    def on_QuitDialog_delete_event(self, widget, *args):
        self.QuitDialog.destroy()
    
    def on_dialog_okbutton1_clicked(self, widget, *args):
        self.quit()
    
class AboutDialog(SimpleGladeApp):
    def __init__(self, path="gvr_gtk.glade", root="AboutDialog", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)

    def new(self):
        # label = self.text_label
        txt = version.ABOUT_TEXT % app_version
        self.text_label.set_text(txt)
        self.text_label.show()
        self.AboutDialog.show()
   
    def on_AboutDialog_delete_event(self, widget, *args):
        self.AboutDialog.destroy()
   
class FileDialog(gtk.FileChooserDialog):
    def __init__(self,action='open',title='',path=os.path.expanduser('~'),ext='wld'):
        #print "FileChooserDialog called",action,title,path,ext
        if action == 'open':
            act = gtk.FILE_CHOOSER_ACTION_OPEN
            but = gtk.STOCK_OPEN
        else:
            act = gtk.FILE_CHOOSER_ACTION_SAVE
            but = gtk.STOCK_SAVE
        gtk.FileChooserDialog.__init__(self,title=title,action=act,
                                  buttons=(gtk.STOCK_CANCEL,
                                        gtk.RESPONSE_CANCEL,
                                        but,
                                        gtk.RESPONSE_OK))
        try:
            startpath = utils.PROGRAMSDIR
        except:
            startpath = os.path.join(utils.get_rootdir())
        self.set_current_folder(startpath)
        wfilter = gtk.FileFilter()
        wfilter.set_name(_("Worlds"))
        wfilter.add_pattern('*.wld')
        self.add_filter(wfilter)

        pfilter = gtk.FileFilter()
        pfilter.set_name(_("Programs"))
        pfilter.add_pattern('*.gvr')
        self.add_filter(pfilter)
        
        if ext == 'wld':
            self.set_filter(wfilter)
        else:
            self.set_filter(pfilter)

class TextEditorWin(SimpleGladeApp):
    def __init__(self, path="gvr_gtk.glade", root="EditorWin", domain=app_name,parent=None, **kwargs):
        path = os.path.join(glade_dir, path)
        self.logger = logging.getLogger("gvr_gtk.TextEditorWin")
        self.parent = parent
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)
        # loaded_file_path is used to determine the path to save to
        # It's set by set_text and save_as* methods.
        self.loaded_file_path = ''
        self.loaded_txt = []

    def new(self):
        """This implements a gtksourceview widget from Editors.py"""
        #Called by SimpleGladeApp
        # We use different editors on win32 as gtksourceview isn't available
        # Editors can be Editors.py or Win_Editors.py, see import statement above
        self.editor = Editors.Editor(self.scrolledwindow1)
        self.observers = []
    
    def set_title(self,title):
        self.EditorWin.set_title(title)
    def get_all_text(self):
        try:
            txt = self.editor.get_all_text()
        except:
            txt = []
        return txt
    def set_text(self,path,txt):
        # path is the path from which the txt comes, we use it to determine
        # the path to save to.
        self.loaded_file_path = path
        self.editor.set_text(txt)
        # used to compare the contents of the editor when quiting
        # We first set the text and then get it again because we compare it
        # against the text returnt by a call to get_all_text
        self.loaded_txt = self.get_all_text()
    def register_observer(self,obs):
        """Register a observer.
        Observer object must be a callable function which takes no arguments.
        Observer will be notified when this object gets destroyed.
        Needed by the worldbuilder and MainWin."""
        self.observers.append(obs)
    def _notify_observers(self):
        try:
            for obs in self.observers:
                apply(obs)
        except Exception,info:
            self.logger.exception("Error in notify observers")
    def show_info(self):
        txt = "Sorry, not yet implemented\nUse the right mousebutton"
        Widgets.InfoDialog(txt=txt)
    
##    def on_TextEditorWin_delete_event(self, widget, *args):
##        self.on_quit2_activate(widget)
    
    # These two methods will be overridden by the child class.
    # It's only needed to connect the methods to the events in SimpleGladeApp
    def on_new1_activate(self,widget,*args):
        pass
    def on_open1_activate(self,widget,*args):
        pass
        
    def on_save1_activate(self, widget=None, txt=[]):
        if txt == []:
            txt = self.get_all_text()
            # used to compare the contents of the editor when quiting
            # We first set the text and then get it again because we compare it
            # against the text returnt by a call to get_all_text
            self.loaded_txt = txt 
        if txt == []:
            Widgets.WarningDialog(txt=_("No content to save"))
            return
        if self.loaded_file_path:
            ext = '.'+str(self)
            if not self.loaded_file_path.endswith(ext):
                self.loaded_file_path = self.loaded_file_path+ext
            status = utils.save_file(self.loaded_file_path,txt)
            if status:
               Widgets.ErrorDialog(txt=status)
            else:
                return True
        else:
            self.on_save_as1_activate(txt=txt)
    
    def on_save_as1_activate(self, widget=None, txt=[]):
        #print "save_as1_activate", txt
        dlg = FileDialog(action='save',title=_('Choose a file'),ext=str(self))
        response = dlg.run()
        if response == gtk.RESPONSE_OK:
            path = dlg.get_filename()
        elif response == gtk.RESPONSE_CANCEL:
            self.logger.debug('Closed, no files selected')
            dlg.destroy()
            return True
        dlg.destroy()
        self.loaded_file_path=path
        if self.on_save1_activate(txt=txt):
            self.set_title(path)
  
    def on_quit2_activate(self, widget=None, *args):
        edittxt = self.get_all_text()
        #print 'edittxt',edittxt
        #print 'loaded_txt',self.loaded_txt
        if edittxt != self.loaded_txt:
            dlg = Widgets.YesNoDialog(txt=_("The %s editor's content is changed.\nDo you want to save it?" % self.name()))
            response = dlg.run()
            dlg.destroy()
            if response == gtk.RESPONSE_YES:
                self.on_save_as1_activate(txt=edittxt)
            else:
                return True
   
    def on_cut1_activate(self, widget, *args):
        self.editor.srcview.emit('cut-clipboard')
    
    def on_copy1_activate(self, widget, *args):
        self.editor.srcview.emit('copy-clipboard')
    
    def on_paste1_activate(self, widget, *args):
        self.editor.srcview.emit('paste-clipboard')
    
    def on_delete1_activate(self, widget, *args):
        self.editor.srcview.emit('delete-from-cursor',gtk.DELETE_CHARS,1)
                               
    def on_print1_activate(self, widget, *args):                            
        import time,tempfile
        head = '\nfile: %s\ndate: %s\n' % \
            (self.EditorWin.get_title().split(' ')[0],time.asctime())
        txt = '\n'.join(self.get_all_text())
        text = '-'*79 + '\n' + head + '-'*79 + '\n' + txt
        # create a secure tempfile, not really needed but I think you should
        # always try to avoid race conditions in any app.
        fd,fn = tempfile.mkstemp()
        fo = os.fdopen(fd,'w')
        try:
            fo.write(text)
            fo.close()
        except Exception,info:
            print info
            return
        utils.send_to_printer(fn)
        os.remove(fn)
        
    def on_about2_activate(self,*args):
        pass
    
    def reset_highlight(self):
        self.editor.reset_highlight()

class CodeTextEditorWin(TextEditorWin):
    def __init__(self, path="gvr_gtk.glade", root="EditorWin", domain=app_name,parent=None, **kwargs):
        TextEditorWin.__init__(self,path,root,domain,parent,**kwargs)
        self.parent = parent
        self.EditorWin.remove(self.vbox4)
        # make sure we don't add > 1 children
        for child in self.parent.alignment19.get_children():
            self.parent.alignment19.remove(child)
        self.parent.alignment19.add(self.vbox4)
    def __str__(self):
        return 'gvr'
    def name(self):
        return 'Code'
    def on_new1_activate(self, widget=None, file=''):
        self.on_quit2_activate()
        self.parent.new_program_editor()
    
    def on_open1_activate(self, widget=None,file=''):
        if not file:
            dlg = FileDialog(action='open',title=_("Open GvR program"),ext='gvr')
            response = dlg.run()
            if response == gtk.RESPONSE_OK:
                file = dlg.get_filename()
                if os.path.splitext(file)[1] != '.gvr':
                    self.show_error(_("Selected path is not a program file"))
                    dlg.destroy()
                    return
            elif response == gtk.RESPONSE_CANCEL:
                self.logger.debug('Closed, no files selected')
                dlg.destroy()
                return
            dlg.destroy()
        txt = utils.load_file(file)
        if txt:
            self.set_text(file,txt)
        for b in ('execute','step','abort'):
            self.parent._set_sensitive_button(b,True)
        return
       
class WorldTextEditorWin(TextEditorWin):
    def __init__(self, path="gvr_gtk.glade", root="EditorWin", domain=app_name,parent=None, **kwargs):
        TextEditorWin.__init__(self,path,root,domain,parent,**kwargs)
        self.parent = parent
        self.EditorWin.remove(self.vbox4)
        # make sure we don't add > 1 children
        for child in self.parent.alignment18.get_children():
            self.parent.alignment18.remove(child)
        self.parent.alignment18.add(self.vbox4)
    def __str__(self):
        return 'wld'
    def name(self):
        return 'World'
    def on_new1_activate(self,widget=None,file=''):
        self.on_quit2_activate()
        self.parent.new_world_editor()
   
    def on_open1_activate(self,widget=None,file=''):
        self.on_quit2_activate()# this takes care of saving content yes/no
        if not file:
            dlg = FileDialog(action='open',title=_("Open GvR world"),ext='wld')
            response = dlg.run()
            if response == gtk.RESPONSE_OK:
                file = dlg.get_filename()
                if os.path.splitext(file)[1] != '.wld':
                    self.show_error(_("Selected path is not a world file"))
                    dlg.destroy()
                    return
            elif response == gtk.RESPONSE_CANCEL:
                self.logger.debug('Closed, no files selected')
                dlg.destroy()
                return
            dlg.destroy()
        txt = utils.load_file(file)
        if txt:
            self.set_text(file,txt)
            self.parent.on_button_reload()
        return
        
class SetLanguageDialog(SimpleGladeApp):
    def __init__(self, path="gvr_gtk.glade", root="SetLanguageDialog", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)

    def new(self):
        #print "A new SetLanguageDialog has been created"
        pass
    
    def get_choice(self):
        try:
            choice = {'Catalan':'ca','Dutch':'nl','English':'en','French':'fr',\
                    'Norwegian':'no','Romenian':'ro','Spanish':'es','Italian':'it'}\
                    [Widgets.get_active_text(self.comboboxentry_language)]
        except Exception,info:
            print info
            choice = 'en'
        return choice
    
    def on_SetLanguageDialog_delete_event(self, widget, *args):
        self.SetLanguageDialog.destroy()
    
    def on_okbutton3_clicked(self, widget, *args):
        pass
    
class SetSpeedDialog(SimpleGladeApp):
    def __init__(self, path="gvr_gtk.glade", root="SetSpeedDialog", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)

    def new(self):
        choice = {_('Instant'):0,_('Fast'):1,_('Medium'):2,_('Slow'):3}[Globals.speed]
        self.comboboxentry_speed.set_active(choice)
    
    def get_choice(self):
        try:
            txt = Widgets.get_active_text(self.comboboxentry_speed)
            choice = {'Instant':5,'Fast':50,'Medium':150,'Slow':500}[txt]
        except Exception,info:
            print info
            choice = 150
        Globals.speed = _(txt)
        return choice
    
    def on_SetSpeedDialog_delete_event(self, widget, *args):
        self.SetSpeedDialog.destroy()
    
    def on_okbutton4_clicked(self, widget, *args):
        pass
    

class SummaryDialog(SimpleGladeApp):
    def __init__(self, path="gvr_gtk.glade", root="SummaryDialog", domain=app_name, **kwargs):
        path = os.path.join(glade_dir, path)
        SimpleGladeApp.__init__(self, path, root, domain, **kwargs)

    def new(self):
        pass
    
    def set_text(self,txt):
        # first line is also used as the title
        title = txt.split('\n')[0]
        buffer = gtk.TextBuffer(table=None)
        try:
            txt = ''.join(txt)
            utxt = unicode(txt)
        except Exception,info:
            print "Failed to set text in source buffer"
            print info
            return
        self.SummaryDialog.set_title(title)
        buffer.set_text(utxt)
        self.textview1.set_buffer(buffer)
    
    def on_SummaryDialog_delete_event(self, widget, *args):
        self.SummaryDialog.destroy()

def main():
    main_win = WindowXO()

    # SimpleGladeApp.run() must be called just once per program
    main_win.run()

if __name__ == "__main__":
    main()

