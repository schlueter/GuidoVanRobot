## This module holds the different help text used by gvr in the menu
DEBUG = 0
import os
from utils import get_rootdir
import logging

module_logger = logging.getLogger("gvr.Text")

OnRefText = ''# this will be set to some text in set_summary() 
InfoFooter = "For more info, http://gvr.sf.net"
OnRefTitle = "Guido van Robot Programming Summary"

OnWBText = ''# this will be set to some text in set_summary() 
OnIntroText = ''

# Builtin summary text, we use it in case of IO trouble.
BuiltinOnRefText = \
"""Guido van Robot Programming Summary
The Five Primitive Guido van Robot Instructions:

   1. move
   2. turnleft
   3. pickbeeper
   4. putbeeper
   5. turnoff

Block Structuring

Each Guido van Robot instruction must be on a separate line.
A sequence of Guido van Robot instructions can be treated as a single
instruction by indenting the same number of spaces.   
<instruction> refers to any of the five primitive instructions above,
the conditional branching or iteration instructions below, or a user
defined instruction.

    <instruction>
    <instruction>
      ...
    <instruction>

Conditionals

GvR has eighteen built-in tests that are divided into three groups: 
the first six are wall tests, the next four are beeper tests, and the last
eight are compass tests:

   1. front_is_clear
   2. front_is_blocked
   3. left_is_clear
   4. left_is_blocked
   5. right_is_clear
   6. right_is_blocked
   7. next_to_a_beeper
   8. not_next_to_a_beeper
   9. any_beepers_in_beeper_bag
  10. no_beepers_in_beeper_bag
  11. facing_north
  12. not_facing_north
  13. facing_south
  14. not_facing_south
  15. facing_east
  16. not_facing_east
  17. facing_west
  18. not_facing_west

Conditional Branching

Conditional branching refers to the ability of a program to alter it's flow
of execution based on the result of the evaluation of a conditional.
The three types of conditional branching instructions in Guido van Robot are
if and if/else and if/elif/else.   
<test> refers to one of the eighteen conditionals above.

if <test>:
    <instruction>

if <test>:
    <instruction>
else:
    <instruction>

if <test>:
    <instruction>
elif <test>:
    <instruction>
...
elif <test>:
    <instruction>
else:
    <instruction>


Iteration

Iteration refers to the ability of a program to repeate an instruction
(or block of instructions) over and over until some condition is met.
The two types of iteration instructions are the do and while instructions.
<positive_number> must be an integer greater than 0.

do <positive_number>:
    <instruction>

while <test>:
    <instruction>

Defining a New Instruction:

New instructions can be created for Guido van Robot using the define statement.
<new_name> can be any sequence of letters or digits as long as it begins with
a letter and is not already used as an instruction.
Letters for Guido van Robot are A..Z, a..z, and the underscore (_) character.
Guido van Robot is case sensitive, so TurnRight, turnright, and turnRight are
all different names.

define <new_name>:
    <instruction>
"""

BuiltinOnWBText = \
"""Guido van Robot Worldbuilder Summary
Editing world:
    Left mouse button : Add or remove walls 
    Middle mouse button: Set arguments for the robot statement
    Right mouse button: Set arguments for the beeper statement
        It's possible to alter the number of beepers by clicking
        the right mouse button when the mouse pointer is at a
        beepers location.
        Give another number of beepers in the beeper dialog.
        When you give 0 (zero) the beeper is removed from the world.
    
Buttons:
    Reload   : Reload the world from the editor window
               into the worldbuilder.
    Abort    : Quit the worldbuilder, *not* GvRng.

"""

BuiltinOnIntroText=\
"""Welcome to the Guido van Robot world.

Guido van Robot, or GvR for short, is a programming language
and free software application designed to introduce beginners
to the fundamentals of programming.
GvR runs on GNU/Linux, XO, Windows, and Macintosh, in a variety
of languages!
It's great in both the classroom and the home as a way of
introducing people to the basic concepts of programming.

At this point, you are probably asking yourself, 
What is GvR, specifically? 
The gist of it is that it is a robot represented by a triangle
on the screen that moves around in a world made up of streets
and avenues, walls and beepers, which Guido can collect or set.
His actions are completely guided by a program written by the
user.

GvR comes with 18 lessons and assignments and a language
reference.
See the "Lessons" tab and start with lesson 1.
Use the "Language reference" tab to get a overview of the GvR
language.

Additional help and information:
OLPC: http://wiki.laptop.org/go/Guido_van_Robot
GvR web page: http://gvr.sourceforge.net/index.php
GvR contact: http://gvr.sourceforge.net/contact/
GvR project page: http://sourceforge.net/projects/gvr/

"""


def set_summary(olang):
    """Get the proper summary file for the current locale"""
    global OnRefText
    # Quick hack to fix the loading of Summary.txt, should be done trying all
    # components of the locale, probably removing the -LANG suffix, as the
    # language is already on the locale dir and putting it in two places makes
    # things harder; is best to use the directory to choose the language or
    # put all the Summaries on the same dir.
    try:
        lang = olang.split('@')[0].split('.')[0].split('_')[0]
    except Exception,info:
        print info
        print "Can't load Summary for language '%s'" % lang
        print "Using default English file"
        lang = 'en'
    sumfile = "Summary-%s.txt" % lang
    if lang == 'en':
        path = os.path.join(get_rootdir(),'po',sumfile)
    else:
        path = os.path.join(get_rootdir(),'po',lang,sumfile)
    if DEBUG: print "trying to read",path
    try:
        lines = open(path,'r').read()
    except IOError,info:
        print info
        print "Can't load Summary for language '%s'" % lang
        print "Using default English file"
        OnRefText = BuiltinOnRefText
    else:
        OnRefText = lines

def set_WBsummary(olang):
    """Get the proper Worldbuilder summary file for the current locale"""
    global OnWBText
    # Quick hack to fix the loading of Summary.txt, should be done trying all
    # components of the locale, probably removing the -LANG suffix, as the
    # language is already on the locale dir and putting it in two places makes
    # things harder; is best to use the directory to choose the language or
    # put all the Summaries on the same dir.
    try:
        lang = olang.split('@')[0].split('.')[0].split('_')[0]
    except Exception,info:
        print info
        print "Can't load Worldbuilder Summary for language '%s'" % lang
        print "Using default English file"
        lang = 'en'
    sumfile = "WBSummary-%s.txt" % lang
    if lang == 'en':
        path = os.path.join(get_rootdir(),'po',sumfile)
    else:
        path = os.path.join(get_rootdir(),'po',lang,sumfile)
    if DEBUG: print "trying to read",path
    try:
        lines = open(path,'r').read()
    except IOError,info:
        print info
        print "Can't load Worldbuilder Summary for language '%s'" % lang
        print "Using default English file"
        OnWBText = BuiltinOnWBText
    else:
        OnWBText = lines

def set_Intro(olang):
    """Get the proper intro text file for the current locale"""
    global OnIntroText
    # Quick hack to fix the loading of Summary.txt, should be done trying all
    # components of the locale, probably removing the -LANG suffix, as the
    # language is already on the locale dir and putting it in two places makes
    # things harder; is best to use the directory to choose the language or
    # put all the Summaries on the same dir.
    try:
        lang = olang.split('@')[0].split('.')[0].split('_')[0]
    except Exception,info:
        print info
        print "Can't load Intro text for language '%s'" % lang
        print "Using default English file"
        lang = 'en'
    sumfile = "Intro-%s.txt" % lang
    if lang == 'en':
        path = os.path.join(get_rootdir(),'po',sumfile)
    else:
        path = os.path.join(get_rootdir(),'po',lang,sumfile)
    if DEBUG: print "trying to read",path
    try:
        lines = open(path,'r').read()
    except IOError,info:
        print info
        print "Can't load intro for language '%s'" % lang
        print "Using default English file"
        OnIntroText = BuiltinOnIntroText
    else:
        OnIntroText = lines

    
    
    
