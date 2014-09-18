'''
GuiWorld is a thin object that delegates most of its 
work to a World object and a WorldDisplay object.

You pass it into a Stepper, and the Stepper calls back
to it when it needs to do the next instruction.  

GuiWorld.MOVE() is the best method to study.  Run GvR
with a program that moves the robot, then get a 
traceback from GuiWorld.MOVE()
'''
import gvrparser
import cheat

class GuiWorldException(Exception):
    def __init__(self, str): self.str = str
    def __str__(self): return self.str

class TurnedOffException: pass

class GuiWorld:
    def __init__(self, gui, logicalWorld):
        self.world = logicalWorld
        self.gui = gui
        for cond in gvrparser.TESTS:
            setattr(self, cond, getattr(self.world, cond))
        self.myCheat = cheat.Cheat()

    def MOVE(self):
        if self.world.front_is_blocked():
            self.abort(_("Ran into a wall"))
        else:
            oldCoords = self.world.robot
            self.world.MOVE()
            self.gui.updateWorldBitmapAfterMove(oldCoords)

    def TURNLEFT(self):
        self.world.TURNLEFT()
        self.gui.updateWorldBitmapAfterMove()

    def PUTBEEPER(self):
        if not self.world.PUTBEEPER():
            self.abort(_("No beepers to put down."))
        else:
            self.gui.updateWorldBitmapAfterBeeper()

    def PICKBEEPER(self):
        if not self.world.PICKBEEPER():
            self.abort(_("No beepers to pick up."))
        else:
            self.gui.updateWorldBitmapAfterBeeper()

    def TURNOFF(self):
        raise TurnedOffException

    def abort(self, msg): raise GuiWorldException(msg)

    def cheat(self, command):
        self.myCheat(command, self)
