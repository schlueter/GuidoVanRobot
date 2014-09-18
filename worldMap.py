# Copyright 2010 S. Zytkiewicz stas.zytkiewicz@gmail.com
#  Copyright (C) 2001 Steve Howell
#  You must read the file called INFO.txt before distributing this code.
# ---
# Worlds for Karel are defined with simple text files that we parse out
# in this module.  See the worlds folder for examples.

from world import NORTH,SOUTH,EAST,WEST
from utils import trace_error
import types
import re,gettext

# Use this to be able to extract strings for translation by pygettext.py
try:
    #print "current _", _
    old_ = _
except Exception,info:
    print >> sys.stderr, "in gvrparser locale switch:\n",info
_ = gettext.gettext 
KEYWORDS = (
        _('ROBOT'),
        _('WALL'),
        _('BEEPERS'),
        _('SIZE'))
DIRECTIONS = (NORTH,SOUTH,EAST,WEST)

####################### Start I18N part #####################################      
# Now we install a gettext file in the builtin namespace
# If this fails the bogus '_()' function is used and we end up with a english - english
# look-up table :-(
# A possible solution would be to test for locales but i think it won't matter much in speed.

_ = old_
#print _
# get a list with the translated strings
trans_commands, org_commands = [],[]
words = KEYWORDS
for i in words:
    trans_commands.append(_(i))
    org_commands.append(i) # this is the english one
# With this we build a look-up dictionary that is used in the Program class.
# The look-up dict: {'beweeg':'move','rechtsaf':turnright',....}
# the keys are the gettext strings and the vals are the original names.
lookup_dict = {}
for k,v in map(None,trans_commands,org_commands):
    lookup_dict[k] = v
lookup_dir_dict = {_('N'):'N',_('S'):'S',_('E'):'E',_('W'):'W'}# 


class WorldMapException(Exception):
    def __init__(self, line, str): 
        self.line = line
        self.str = str
    def __str__(self): return self.str

def checkDirection(line, dir):
    if dir not in lookup_dir_dict.values():
        raise WorldMapException(line, 
            _("In line %d:\n%s is not a valid direction -- use N, S, E, or W")
            % (line, dir))

def removeComment(line):
    foundComment = False
    for i in range(len(line)):
        if line[i] == "#": 
            foundComment = True
            break
    if foundComment:
        return line[:i]
    else:
        return line

def readWorld(lines, world):
    definedRobot = 0
    useGuido = False
    linenumber = 0
    worldSize = None
    for line in lines:
        linenumber += 1
        try:
            if re.search("\S", line) and not re.match("\s*#", line):
                line = removeComment(line)
                tokens = line.split()
                tokens = [x.upper() for x in tokens]
                keyword = tokens[0]
                if lookup_dict.has_key(keyword):
                    keyword = lookup_dict[keyword]
                if keyword == _('ROBOT') or keyword == 'ROBOT':
                    if len(tokens) < 4:
                        raise WorldMapException(linenumber,_('Robot direction argument missing'))
                    dir = tokens[3]
                    if lookup_dir_dict.has_key(dir):
                        dir = lookup_dir_dict[dir]
                        tokens[3] = dir
                    else:
                        print lookup_dir_dict.has_key(dir), lookup_dir_dict, dir
                        raise WorldMapException(linenumber, _('No valid direction given for the robot'))
                if keyword ==_('WALL') or keyword == 'WALL':
                    tokens[0] = keyword
                    #print "wall",tokens
                    checkDirection(linenumber, dir)
                    #print "tokens",tokens
                    if len(tokens) < 3:
                        raise WorldMapException(linenumber,_('Too little %s arguments' % _('WALL')))
                    else:
                        if len(tokens) == 5:
                            try:
                                int(tokens[4])
                            except ValueError:
                                raise WorldMapException(linenumber, _('%s length argument must be an integer' % _('WALL')))
                            else:
                                if int(tokens[4]) < 1:
                                    raise WorldMapException(linenumber,_('%s length argument must be greater than zero' % _('WALL')))
                    world.setWall(*tokens[1:])
                elif keyword == _('ROBOT') or keyword == 'ROBOT':
                    if definedRobot:
                        raise WorldMapException(linenumber, _('You may only have one robot definition.'))
                    definedRobot = 1
                    tokens = [x.upper() for x in tokens]
                    if len(tokens) == 5:
                        x, y, dir, numBeepers = tokens[1:]
                    else:
                        x, y, dir = tokens[1:]
                        numBeepers = 0
                    robotX, robotY = int(x), int(y)
                    world.positionRobot(robotX, robotY, dir)
                    if numBeepers == "unlimited":
                        world.unlimitedBeepers = True
                        numBeepers = 0
                    world.setRobotBeepers(int(numBeepers))
                elif keyword == _('BEEPERS') or keyword == 'BEEPERS':
                    x, y, numBeepers = tokens[1:]
                    world.setBeepers(int(x), int(y), int(numBeepers))
                elif keyword == 'BDFL':
                    useGuido = True
                elif keyword == _('SIZE') or keyword == 'SIZE':
                    if worldSize:
                        raise WorldMapException(linenumber,
                            _('You may only have one size statement'))
                    try:
                        avenues, streets = [int(coord) for coord in tokens[1:]]
                    except ValueError:
                        raise WorldMapException(linenumber,
                            _('Size statement should have 2 integers')) 
                    if avenues < 7 or streets < 7:
                        raise WorldMapException(linenumber,
                            _('Size coordinates must be at least 7'))
                    worldSize = (avenues, streets)
                else:
                    raise WorldMapException(linenumber,_("Cannot understand: %s") % line)
        except (WorldMapException, Exception),e:
            #trace_error()
            info = _("Error: %s\n in line %s: %s\nCheck your world file for syntax errors") % (e, linenumber,line)
            raise WorldMapException(linenumber, info)
    if not definedRobot:
        raise WorldMapException(linenumber, _("The world map seems to be missing information."))
    world.useGuido = useGuido
    return worldSize
