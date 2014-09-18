#  Copyright (C) 2001 Steve Howell
# Copyright (C) 2007-2010 Stas Zytkiewicz
#  You must read the file called INFO.txt before distributing this code.

## Added a few abstraction methods in World to be used in the new MVC design
## The addition is also needed to prevent frontends importing WEST and SOUTH
## constants needed to get the wall positions.
## Nothing else was changed. Stas

import os,sys,time

##NORTH = _('N')
##WEST  = _('W')
##SOUTH = _('S')
##EAST  = _('E')
NORTH = 'N'
WEST  = 'W'
SOUTH = 'S'
EAST  = 'E'

class WorldMapException(Exception):
    """We use this because stuff in here is related to stuff in the worldMap module.
    So we can cache this exception when doing world/worldMap things."""
    pass
    #def __init__(self, str): self.str = str
    #def __str__(self): return self.str
    
class World:
    '''
    A World is an abstract environment for Guido to move around it.

    positionRobot, setWall, setBeepers, setRobotBeepers set up
       the intial environment

    MOVE, TURNLEFT, PICKBEEPER, and PUTBEEPER change the 
       environment

    methods corresponding to the GvR conditionals such as
    FACING_NORTH, RIGHT_IS_CLEAR, etc. allow you to check
    the environment from the robot's perspective

    self.robot, self.robotBeepers, self.beepers, and self.walls
    are considered public attributes
    '''
    wall = {}
    """
    The offsets here are due to the fact we only want to think
    of walls as being south or west of current squares, so that 
    there's no ambiguity about how a wall is named.  For example,
    the wall to the right of 1,1 is east of 1,1, but it's also 
    to the west of 2,1.  We only want to think of it as being 
    the wall to the west of 2,1.  Therefore, when we go to put 
    a wall to the east of (1,1), we see that the offset for 
    wall[EAST] is (1,0), and then we know that the wall is really
    west of (2,1) for our purposes.
    """
    wall[NORTH] = (0,1)
    wall[EAST]  = (1,0)
    wall[SOUTH] = (0,0)
    wall[WEST]  = (0,0)
    """
    Continuing the thought above, we treat E/W walls only as being
    westerly walls, and we treat N/S walls only as being southerly 
    walls.
    """
    direction = {}
    direction[NORTH]   = SOUTH
    direction[EAST]    = WEST
    direction[SOUTH]   = SOUTH
    direction[WEST]    = WEST
    delta = {}
    delta[NORTH] = (0,1)
    delta[EAST]  = (1,0)
    delta[SOUTH] = (0,-1)
    delta[WEST]  = (-1,0)
    left = {}
    left[NORTH] = WEST
    left[EAST]  = NORTH
    left[SOUTH] = EAST
    left[WEST]  = SOUTH
    right = {}
    right[NORTH] = EAST
    right[EAST]  = SOUTH
    right[SOUTH] = WEST
    right[WEST]  = NORTH

    def __init__(self):
        self.robot = (0,0)
        self.dir = ''
        self.robotBeepers = 0
        self.beepers = {}
        self.unlimitedBeepers = False
        self.walls = {WEST:{},SOUTH:{}}
        self.useGuido = False
        
    #----- abstraction methods 
    def get_robots_position(self):
        return self.robot
    def get_robots_direction(self):
        return self.dir
    def get_robots_beepers(self):
        return self.robotBeepers
    def get_walls_position(self):
        return {'west_wall':self.walls[WEST],
                'south_wall':self.walls[SOUTH]}
    def get_beepers(self):
        return self.beepers
    #---- utility method

    def _adjust(self, coords, adj):
        (x,y) = coords
        (adjX, adjY) = adj
        return (x+adjX, y+adjY)

    #----- walls
    def setWall_wb(self, x, y, dir):
        """Same as setWall but used by the worldbuilder to determine if
        a wall should be removed"""
        x = int(x)
        y = int(y)
        #print "setWall_wb",dir,NORTH,SOUTH
        if dir in(NORTH, SOUTH):
            coords = (x,y)
        else:
            coords = (x,y)
        return self.setSingleWall(coords, dir)
    
    def setWall(self, x, y, dir, length = 1):
        x = int(x)
        y = int(y)
        length = int(length)
        for offset in range(length): 
            if dir in(NORTH, SOUTH):
                coords = (x+offset,y)
            else:
                coords = (x,y+offset)
            self.setSingleWall(coords, dir)

    def buildWallOnLeft(self):
        '''
        This method builds a wall to the left of the
        robot's current ##location.
        '''
        dir = World.left[self.dir]
        return self.setSingleWall(self.robot, dir)

    def buildWallOnRight(self):
        '''
        This method builds a wall to the right of the
        robot's current location.
        '''
        dir = World.right[self.dir]
        return self.setSingleWall(self.robot, dir)

    def setSingleWall(self, coords, dir):
        coords = self._adjust(coords, World.wall[dir])
        dir = World.direction[dir]
        try:
            # this test is needed as the worldbuilder also removes walls
            if self.walls[dir][coords] == 1:
                del self.walls[dir][coords]
                return (dir, coords,0)
        except KeyError:
            self.walls[dir][coords] = 1
        return (dir, coords,1)

    #----- beepers

    def setBeepers(self, x, y, numBeepers):
        self.beepers[(x,y)] = numBeepers

    def setRobotBeepers(self, numBeepers):
        self.robotBeepers = numBeepers

    #----- robot

    def positionRobot(self, x, y, dir):
        if x < 1:
            raise WorldMapException (_("Bad x value for positioning robot: %s") % x)
        if y < 1:
            raise WorldMapException (_("Bad y value for positioning robot: %s") % y)
        self.robot = (x,y)
        self.dir = dir

    #----- builtin commands

    def MOVE(self):
        if self.front_is_blocked(): return 0
        self.robot = self._adjust(self.robot, World.delta[self.dir])
        return 1

    def TURNLEFT(self):
        self.dir = World.left[self.dir]

    def PICKBEEPER(self):
        (x,y) = self.robot
        if self.beepers.has_key((x,y)) and self.beepers[(x,y)] >= 1:
            self.robotBeepers += 1
            self.beepers[(x,y)] -= 1
            if self.beepers[(x,y)] == 0:
                del self.beepers[(x,y)]
            return 1
        else:
            return 0
            
    def PUTBEEPER(self):
        (x,y) = self.robot
        if self.unlimitedBeepers:
            self.beepers[(x,y)] = self.beepers.get((x,y), 0) + 1
            return 1
        if self.robotBeepers == 0: return 0
        self.robotBeepers -= 1
        self.beepers[(x,y)] = self.beepers.get((x,y), 0) + 1
        return 1

    #------ test conditions
            
    def _is_blocked(self, dir):
        (x,y) = self._adjust(self.robot, World.wall[dir])
        dir=World.direction[dir]
        if y<=1 and dir==SOUTH:
            return 1
        if x<=1 and dir==WEST:
            return 1
        return self.walls[dir].get((x,y), 0)

    def facing_north(self):
        return self.dir == NORTH
    
    def facing_east(self):
        return self.dir == EAST

    def facing_south(self):
        return self.dir == SOUTH

    def facing_west(self):
        return self.dir == WEST
    
    def front_is_blocked(self):
        return self._is_blocked(self.dir)

    def front_is_clear(self):
        return not World.front_is_blocked(self)

    def not_facing_north(self):
        return self.dir != NORTH
    
    def not_facing_east(self):
        return self.dir != EAST

    def not_facing_south(self):
        return self.dir != SOUTH

    def not_facing_west(self):
        return self.dir != WEST
    
    def left_is_blocked(self):
        return self._is_blocked(World.left[self.dir])
        
    def left_is_clear(self):
        return not World.left_is_blocked(self)

    def right_is_blocked(self):
        return self._is_blocked(World.right[self.dir])

    def right_is_clear(self):
        return not World.right_is_blocked(self)
    
    def any_beepers_in_beeper_bag(self):
        return self.robotBeepers > 0

    def no_beepers_in_beeper_bag(self):
        return self.robotBeepers == 0
    
    def next_to_a_beeper(self):
        try:
            (x,y) = self.robot
            return self.beepers[(x,y)] > 0
        except: return 0

    def not_next_to_a_beeper(self):
        return not World.next_to_a_beeper(self)

    def furthestCoordinate(self):
        westKeys = [(x, y+1) for x,y in self.walls[WEST].keys()]
        southKeys = [(x+1, y) for x,y in self.walls[SOUTH].keys()]
        beeperKeys = [(x+1, y+1) for x,y in self.beepers.keys()]
        objectLocations = beeperKeys + westKeys + southKeys
        x,y = self.robot
        objectLocations.append((x+1,y+1))
        greatestX = 0
        greatestY = 0
        for x,y in objectLocations:
            if greatestX < x:
                greatestX = x
            if greatestY < y:
                greatestY = y
        return greatestX, greatestY

    def nearestCoordinate(self):
        beeperKeys = [(x-1, y-1) for x,y in self.beepers.keys()]
        westKeys = [(x, y+1) for x,y in self.walls[WEST].keys()]
        southKeys = [(x+1, y) for x,y in self.walls[SOUTH].keys()]
        objectLocations = beeperKeys + westKeys + southKeys
        x,y = self.robot
        objectLocations.append((x-1,y-1))
        leastX, leastY = objectLocations[0]
        x,y = self.robot
        for x,y in objectLocations:
            if leastX > x:
                leastX = x
            if leastY > y:
                leastY = y
        return leastX, leastY

##    def newOffset(self, (offsetX, offsetY), (width, height)):
##        def recenter(robot, offset, size):
##            shift = 0
##            if robot >= size:
##                offset = robot - int(size/2)
##                if offset < 0: offset = 0
##                shift = 1
##            else:
##                offset = 0
##            return shift, offset
##        x,y = self.robot
##        shiftX, offsetX = recenter(x, offsetX, width)
##        shiftY, offsetY = recenter(y, offsetY, height)
##        return (shiftX or shiftY, (offsetX, offsetY))

    def newOffset(self, (offsetX, offsetY), (width, height)):
        x,y = self.robot
        newoffset = [0,0]
        scroll = 0
        if x == width:
            scroll = 1
            newoffset[0] += 6
        if y == height:
            scroll = 1
            newoffset[1] += 6
        return (scroll,tuple(newoffset))
        
