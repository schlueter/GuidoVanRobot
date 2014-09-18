# -*- coding: utf-8 -*-

# Copyright (c) 2007 Stas Zykiewicz <stas.zytkiewicz@gmail.com>
#
#           GvrModel.py
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
This is the model, as in MVC, which acts as a interface on top of the original
GvR implementation and talks with the controller (GvrController.py).
The reason for an extra abstracting layer is because gvr was never designed
as a MVC pattern.
Because of that some constructs in here seems a bit strange but it is done
to let the rest of the original gvr code intact.

You should not talk to this object direct but by using the controller.
"""

import utils
#set_locale()
import world,worldMap,stepper,guiWorld, gvrparser
import sys,os,time
import logging

_DEBUG = 0# increase for more info

if _DEBUG:
    import pprint,time
    if os.name == "posix": os.environ["TMP"] = "/tmp"
    debugfile = os.path.join(os.environ["TMP"],"GvrModelDebugLog.txt")

def DebugToFile(seq=[""]):
    """sends the given seq to a file this file is placed in the systems temporary
    directory.
    It uses the 'pprint' standard module to format the sequence.
    """
    try:
        f = open(debugfile,"a")
        print >> f,time.asctime()
        print "Debug output send to %s" % debugfile
        pprint.pprint(seq,f)
    finally:
            f.close()

class Breakpoint(Exception): pass

class GvrModel:
    """This is the model from the MVC pattern.
    Every method in this class returns None on faillure, anything else means succes."""
    def __init__(self,*args):
        """args is optional and not used. It's here for possible future use"""
        self.logger = logging.getLogger("gvr.GvrModel.GvrModel")
        self.logicworld = None
        self.myStepper = None
        # timer interval
        self.interval = 500
    def stop(self):
        """This is called by the controller when the app should exit/stop.
        Do any cleanup here before it returns."""
        pass
    def set_controller(self,contr):
        self.controller = contr  
        return 1
    def set_timer(self):
        self.timer = self.controller.get_timer()
        self.timer.set_func(self.wakeUp)
        self.timer.set_interval(interval=self.interval)
        
    def on_code_execute(self,gui=None,step=None):
        """The controller calls this when the user hits the 'execute' button.
        When step is True the timer isn't started.
        This is the point from where the whole show starts."""
        self.logger.debug("on_code_execute called")
        worldlines = self.controller.get_worldwin_text()
        if _DEBUG > 1: print self.__class__,"worldlines",worldlines
        codelines = self.controller.get_codewin_text()
        if len(worldlines) == 0 or len(codelines) == 0:
            self.controller.give_warning(_("Please load a world and program before executing."))
            return None
        codestring = "\n".join(codelines)
        if _DEBUG > 1: print self.__class__,"codestring",codestring
        logicworld = self.on_world_reload(worldlines)
        if not logicworld:# on_world_reload gives signals the controller in case of error
            return None
        # logicworld is made a class member because stepper doesn't pass the 
        # logicworld object when it calls updateWorldBitmapAfterMove.
        # Because we want all the logic to use the same logicworld object we
        # made it a class member so that updateWorldBitmapAfterMove uses the
        # self.logicworld to pass on to the controller.
        # see also updateWorldBitmapAfterMove and GvrController.word_state_changed
        self.logicworld = logicworld
        # GuiWorld gets a GvrModel reference because it expects a object with a
        # updateWorldBitmapAfterMove(oldcoords) method which it calls when the
        # world state is changed.
        myGuiWorld = guiWorld.GuiWorld(self,logicworld)
        try:
            # stepper can be passed a object to highlight the current line of code
            # This object is 'debugger' which just provides the method stepper
            # calls: setLine
            # See stepper.Stepper.step
            self.myStepper = stepper.Stepper(codestring, myGuiWorld,self.controller)
        except gvrparser.BadCommand,info:
            utils.trace_error()
            self.controller.give_error(str(info))
        else:
            if step:
                return 1
            else:
                self.start_timer()
        #self.controller.draw_world(logicworld)
        return 1
    
    def start_timer(self):
        if _DEBUG: print "start timer called"
        self.set_timer()# will also set self.timer
        self.timer.set_interval(self.controller.get_timer_interval())
        self.timer.start()
            
    def wakeUp(self):
        """This calls stepper.step to execute the lines of code from the gvr 
        program. It caches the stepper exceptions and when needed signals the
        controller that we stop/quit
        This is also called by the controller when the user hits the step button."""        
        #print "wakeUp called"
        if not self.myStepper:
            self.on_code_execute(step=True)
        try:
            self.myStepper.step()
            #self.refresh()
            #self.updateStatusBar()
            #self.startTimer()
        except guiWorld.TurnedOffException:
            self.stopRobot()
            self.controller.give_info(_('Robot turned off'))
        except (guiWorld.GuiWorldException,\
                stepper.OutOfInstructionsException),e:
            self.stopRobot()
            self.controller.give_warning(str(e))
        except Breakpoint:
            pass
            # XXX Not sure what to do here. Stas Z
            #self.Pause()
        except AttributeError:
            # happens when no world is loaded
            self.logger.exception("No world loaded?")
            pass
        else:
            pass
            # place holder for telling controller to update the world ??
        return 1
        
    def stopRobot(self):
        """Stops the robot and does some cleanup."""
        #self.testtimer = 0
        try:
            self.timer.stop()
        except:
            pass
        if _DEBUG: print "stoprobot"
        self.myStepper = None
        #self.stopTimer()
        #self.executeButton.Enable(1)
        #self.pauseButton.Enable(0)
        #self.abortButton.Enable(0)
        #self.reloadButton.Enable(1)
        return 1
    def debug(self, message):
        """Wrapper for debug messages, the message will be put in a dialog from
        the view."""
        self.controller.give_info(message)
        return 1
    def updateWorldBitmapAfterMove(self,oldcoords=None):
        """Wrapper needed because stepper calls it after a move from guido.
        oldcoords are the old robot coords.
        Called from guiWorld.GuiWorld"""
        if not self.logicworld:
            print "no logicworld in GvrModel updateWorldBitmapAfterMove"
            print "This should not happening"
        self.controller.world_robot_state_changed(self.logicworld,oldcoords)
        self.controller.world_beepers_state_changed(self.logicworld)
    
    def updateWorldBitmapAfterBeeper(self):
        """Wrapper needed because stepper calls it after a beeper action from guido.
        oldcoords are the old robot coords.
        Called from guiWorld.GuiWorld"""
        self.controller.world_beepers_state_changed(self.logicworld)
       
    def on_world_reload(self,worldcode):
        """ This will return a world object representing the logic from the
        world code, it also makes it a class attribute.
        @worldcode must be a list of strings."""
        #print self.__class__,'on_world_reload called'
        try:
            logicworld = world.World()
            # worldMap changes/sets the logicworld attributes
            worldMap.readWorld(worldcode, logicworld)
        except Exception,info:
            #print info
            self.controller.give_error(str(info))
            return None
        else:
            self.stopRobot()
            if _DEBUG > 1:
                print "logicworld:"
                print "robot pos",logicworld.get_robots_position()
                print "robot dir",logicworld.get_robots_direction()
            self.logicworld = logicworld
            self.controller.world_state_changed(self.logicworld)
            return self.logicworld
            
    def get_beepers(self):
        """Return the number of beepers the robot has."""
        b = None
        if self.logicworld:
            b = self.logicworld.get_robots_beepers()
        return b
    def get_position(self):
        """Returns the robot position in a tuple."""
        p = None
        if self.logicworld:
            p = (self.logicworld.get_robots_position(),
                self.logicworld.get_robots_direction())
        return p
        
