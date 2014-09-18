# -*- coding: utf-8 -*-

# Copyright (c) 2007 Stas Zykiewicz <stas.zytkiewicz@gmail.com>
#
#           GvrController.py
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


"""
This is a controller from a MVC pattern and 'talks' to GvrModel and a view.
"""

import sys,time
from utils import trace_error
import logging

class Controller:
    """This is the controller (mvc).
    It controls GvrModel.py and a view, the view can be any module which provides
    the methods marked 'View' in the file describing this controller.
    This file is called 'Guidelines_for_View.txt'. You should look at this file
    if you are planning a different view. Also be sure to check the
    'Guidelines_for_main.txt' on how to start these modules.(yet to be written)
    """
    def __init__(self,model,view):
        """Get a reference to the model and view objects.
        The controller uses these to call their methods.
        All controller methods return False on faillure, anything else means
        success."""
        self.logger = logging.getLogger("gvr.GvrController.Controller")
        self.View = view
        self.Model = model
    
    def start_view(self,*args):
        """This ask the view to build/start it's GUI. The view must start an
        eventloop of some sort otherwise the controller stops here.""" 
        self.logger.debug("start view")
        self.View.start(args)
        return True
    
    def quit(self):
        """Stops the view and the model by calling their 'stop' methods.
        Then wait for one second to let every procces stop and return to the
        'main' from where were started."""
        try:
            self.logger.debug("Stopping Guido van Robot...")
            self.View.stop()
        except:
            trace_error()
            pass
        try:
            self.Model.stop()
            time.sleep(1)
            self.logger.debug("Done")
        except:
            self.logger.exception("Failed to quit properly")
            pass
        return True
    ### View callbacks
    def on_button_execute(self):
        """Called by the view when the execute button is pressed.
        This will call model.on_code_execute().
        The model looks for world and program code by calling c.get_*win_text.
        The model also calls c.give_error in case of an error."""
        #self.View.statusbar.set_mesg("Button 'Execute' pressed")# for testing only
        self.logger.debug("button execute")
        self.Model.on_code_execute()
        return True
    def on_button_reload(self,worldcode):
        """Called by the view when the reload button is pressed.
        This will call model.on_world_reload().
        The model will notify the controller.world_state_changed method
        or call c.give_error on any error."""
        self.logger.debug("button reload")
        self.Model.on_world_reload(worldcode)
        return True
    def on_button_step(self):
        """Called by the view when the step button is pressed.
        This will call model.on_button_step()."""
        self.logger.debug("button step")
        self.Model.wakeUp()
        return True
    def on_button_abort(self):
        """Called by the view when the abort button is pressed.
        This will call model.on_abort()."""
        self.logger.debug("button abort")
        self.Model.stopRobot()
        return True
    def get_robot_position(self):
        """Called by the view
        Return the position of the robot in the logic world as a tuple or None"""
        #self.logger.debug("get_robot_position")
        return self.Model.get_position()
    def get_robot_beepers(self):
        """Called by the view.
        Returns the number of beepers the robot is carrying as integer or None."""
        #self.logger.debug("get_robot_beepers")
        return self.Model.get_beepers()
    ## Model callbacks
    def get_worldwin_text(self):# XXX not sure we need this
        """Called by the model and controller.
        This will call View.worldwin_gettext()."""
        txt = self.View.worldwin_gettext()
        if txt:
            return txt
        else:
            return ''
    def get_codewin_text(self):
        """Called by the model.
        This will call View.codewin_gettext()."""
        txt = self.View.codewin_gettext()
        if txt:
            return txt
        else:
            return ''
    def setLine(self,line):
        """Called by the stepper as the model passes this object"""
        self.View.highlight_line_code_editor(line)
    def get_timer(self):
        return self.View.get_timer()
    def get_timer_interval(self):
        return self.View.get_timer_interval()
    def give_warning(self,txt):
        """Called by the model.
        This will call View.show_warning(txt)."""
        self.View.show_warning(txt)
        return True
    def give_error(self,txt):
        """Called by the model.
        This will call View.show_error(txt)."""
        self.View.show_error(txt)
        return True
    def give_info(self,txt):
        """Called by the model.
        This will call View.show_info(txt)."""
        self.View.show_info(txt)
        return True
    def world_state_changed(self,obj):
        """Called by the model.
        This will inform the view that the state of the world is changed.
        (robot is moved)
        This will call View.update_world(obj)
        @obj is a gvr logical world object"""
        #self.logger.debug("world_state_changed called")
        self.View.update_world(obj)
        return True
    def world_robot_state_changed(self,obj,oldcoords=None):
        """Called by the model from updateWorldBitmapAfterMove when stepper
        stepped"""
        #self.logger.debug("world_robot_state_changed called")
        self.View.update_robot_world(obj,oldcoords)
        return True
    def world_beepers_state_changed(self,obj):
        """Idem as world_robot_state_changed"""
        #self.logger.debug("world_beepers_state_changed called")
        self.View.update_beepers_world(obj)
        return True
    
