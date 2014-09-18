# -*- coding: utf-8 -*-

# Copyright (c) 2008 Stas Zykiewicz <stas.zytkiewicz@gmail.com>
#
#           gvrparser.py
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
/*
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Library General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 */
""" 

import re, string, gettext,locale,__builtin__, os, sys,pprint,logging
from utils import LOCALEDIR

module_logger = logging.getLogger("gvr.gvrparser")

global FUNCS #list of user defined functions
FUNCS=[]

def isIterator(token):
    try:
        x = int(token['statement'])
        if x < 0:
            raise BadIterator, token
        else:
            return 1
    except:
        raise BadIterator, token

def isColon(token):
    if token['statement'] != ':':
        raise NoColon, token

def isName(token):
    if re.match("[a-zA-Z_]+[0-9]*", token['statement']):
        return 1
    else:
        raise BadName, token
    
# IMPORTANT
# This is a change from the original code which worked for 4 years but now
# it seems that gettext works somehow differently, python 2.5??? Don't know
# This should be properly tested with non-english languages on various systems.
try:
    #print "current _", _
    # keep old gettext function, we restore it later
    old_ = _
except Exception,info:
    module_logger.error("in gvrparser locale switch:%s" % info)

# Here we override the gettext _ function because we want the original strings first
_ = lambda x:x

TESTS = (
     _('any_beepers_in_beeper_bag'),
     _('facing_north'),
     _('facing_east'),
     _('facing_south'),
     _('facing_west'),
     _('front_is_blocked'),
     _('front_is_clear'),
     _('no_beepers_in_beeper_bag'),
     _('next_to_a_beeper'),
     _('not_next_to_a_beeper'),
     _('not_facing_north'),
     _('not_facing_east'),
     _('not_facing_south'),
     _('not_facing_west'),
     _('left_is_blocked'),
     _('left_is_clear'),
     _('right_is_blocked'),
     _('right_is_clear'),
    )

COMMANDS = (
     _('move'),
     _('pickbeeper'),
     _('putbeeper'),
     _('turnleft'),
     _('turnoff'),
     _('cheat'),
    )
# The tuple DIV contains names/words used in the GvR langauge, but are
# hardcoded somewhere else in this module. We list them here to be able
# to get them with gettext and to put it in the lookup table.
# That's the only usage for this tuple, There are no changes to the way
# the parser works.
DIV = (
     _('define'),
     _('end'),
     _('if'),
     _('elif'),
     _('else'),
     _('while'),
     _('do'),
     _('end'),
    )

####################### Start I18N part #####################################      
# We have replaced the gettext _ with a lambda function that returns the original
# strings.
# So we first get a list with the untranslated strings
trans_commands, org_commands = [],[]
words = COMMANDS + TESTS + DIV
# Now we restore the gettext function again.
# Remember that words now holds the english words.
_ = old_
for i in words:
     trans_commands.append(_(i))# this is the translated string
     org_commands.append(i) # and this is the english one

# With this we build a look-up dictionary that is used in the Program class.
# The look-up dict: {'beweeg':'move','rechtsaf':turnright',....}
# the keys are the gettext strings and the vals are the original names.
lookup_dict = {}
for k,v in map(None,trans_commands,org_commands):
    lookup_dict[k] = v
module_logger.debug("lookup_dict: %s" % lookup_dict)

################################## End of I18N ############################

def parseStatement(token):
    statement = token['statement']
    global FUNCS
    if statement not in COMMANDS and statement not in FUNCS:
        raise BadStatement, token
    return Statement(token)

def parseCheat(token):
    return Cheat(token)

def parseBlock(remainingTokens):
    statements = []
    while len(remainingTokens):
        token = remainingTokens[0]
        curStatement = token['statement']
        parseMethods = {
            'if': parseIfStatement,
            'while': parseWhileLoop,
            'do': parseDoLoop}
        if curStatement in parseMethods:
            method = parseMethods[curStatement]
            parsedObject, remainingTokens = method(remainingTokens)
            statements.append(parsedObject)
        else:
            cmd = token
            if cmd['statement'] == 'cheat':
                remainingTokens = remainingTokens[1:]
                cheat = remainingTokens[0]
                statements.append(parseCheat(cheat))
            else:
                statements.append(parseStatement(cmd))
            remainingTokens = remainingTokens[1:]
    # When there's only a define statement without any toplevel code we just do 
    # nothing. This is much like the Python behaviour.
    try:
        defaultIndent = statements[0].indent
    except:
        pass
    for statement in statements:
        if statement.indent != defaultIndent:
            raise IndentError, statement
    return Block(statements)

def eatLine(tokens, startIndex):
    currentLine = tokens[:startIndex]
    if currentLine[-1]['line'] != currentLine[0]['line']:
        raise LineTooShort, tokens[0]
    if currentLine[-1]['statement'] != ':':
        raise NoColon, tokens[0]
    return currentLine

def eatBlock(tokens, startIndex):
    currentLine = eatLine(tokens, startIndex)
    indent = tokens[0]['indent'] 
    end = startIndex
    while end < len(tokens) and tokens[end]['indent'] > indent:
        end += 1
    if end == startIndex:
        # Report the error as being on the line
        # where you expected the indented command.
        # You can safely assume that there will always
        # be at least one token on the current line,
        # or this would have never been called.
        raise ExpectedBlock , currentLine[0]['line']+1
    block = tokens[startIndex:end]
    restOfCode = tokens[end:]
    return currentLine, block, restOfCode

def parseTestCondition(token):
    statement = token['statement']
    line = token['line']
    if statement not in TESTS:
        raise BadTest, token
    return TestCondition(statement, line)

def parseConditionAndBlock(currentLine, block):
    condition = parseTestCondition(currentLine[1])
    blockObj = parseBlock(block)
    return (currentLine[0]['indent'], condition, blockObj)

def parseIfStatement(tokens):
    currentLine, block, tokens = eatBlock(tokens, 3)
    ifStatement = IfStatement(*parseConditionAndBlock(currentLine, block))
    while len(tokens):
        if tokens[0]['statement'] != 'elif': break
        elifObj, tokens = parseElifStatement(tokens)
        ifStatement.elifs.append(elifObj)
    if len(tokens) and tokens[0]['statement'] == 'else':
        ifStatement.elseObj, tokens = parseElseStatement(tokens)
    return ifStatement, tokens

def parseElseStatement(tokens):
    currentLine, block, remainingTokens = eatBlock(tokens, 2)
    blockObj = parseBlock(block)
    return blockObj, remainingTokens

def parseElifStatement(tokens):
    currentLine, block, remainingTokens = eatBlock(tokens, 3)
    return ElifStatement(*parseConditionAndBlock(currentLine, block)), remainingTokens

def parseWhileLoop(tokens):
    currentLine, block, remainingTokens = eatBlock(tokens, 3)
    condition = parseTestCondition(currentLine[1])
    blockObj = parseBlock(block)
    return WhileLoop(currentLine[0]['indent'], condition, blockObj), remainingTokens

def parseDoLoop(tokens):
    currentLine, block, remainingTokens = eatBlock(tokens, 3)
    iterator = currentLine[1]['statement']
    isIterator(currentLine[1])
    blockObj = parseBlock(block)
    try:
        int(iterator)
    except ValueError, info:
        print info
        raise BadCommand, (currentLine[1], _('Argument for "%s" must be an integer, not %s' % (_('do'), iterator)))
    if int(iterator) < 1:
        raise BadCommand, (currentLine[1], _('Argument for "%s" must be greater than zero' % _('do')))
    return DoLoop(currentLine[0]['indent'], iterator, blockObj), remainingTokens

def parseDefine(tokens):
    currentLine, block, tokens = eatBlock(tokens, 3)
    name = currentLine[1]
    isName(name)
    global FUNCS
    if name['statement'] in FUNCS:
        raise DoubleDefinition, name
    FUNCS.append(name['statement'])
    blockObj = parseBlock(block)
    return Define(name['statement'], blockObj), tokens

def parseProgram(tokens, ignore=None):
    for dict in tokens:
        if lookup_dict.has_key(dict['statement']):
            dict['statement'] = lookup_dict[dict['statement']]
    global FUNCS
    FUNCS = []
    functions = []
    while len(tokens):
        token = tokens[0]
        if token['statement'] == "define":
            blockObj, tokens = parseDefine(tokens)
            functions.append(blockObj)
        else:
            break
    block = parseBlock(tokens)
    return Program(functions, block)

class Statement:
    def __init__(self, token):
        self.indent = token['indent']
        self.statement = token['statement']
        self.line = token['line']

class Cheat(Statement):
    def __init__(self, token):
        self.indent = token['indent']
        self.statement = token['statement']
        self.line = token['line']

class Block:
    def __init__(self, statements):
        self.statements = statements

class TestCondition:
    def __init__(self, statement, line):
        self.statement = statement
        self.line = line


class IfStatement:
    def __init__(self, indent, condition, block):
        self.indent = indent
        self.condition = condition
        self.block = block
        self.elifs = []
        self.elseObj = None

class ElifStatement(IfStatement): pass

class WhileLoop:
    def __init__(self, indent, condition, block):
        self.indent = indent
        self.condition = condition
        self.block = block

class DoLoop:
    def __init__(self, indent, iterator, block):
        self.indent = indent
        self.iterator = iterator
        self.block = block


class Define:
    def __init__(self, name, block):
        self.name = name
        self.block = block
        
class Program:
    def __init__(self, functions, block):
        self.functions = functions
        self.block = block


    
#-- exception handling
#import exceptions

class ParseError(Exception):
    def __init__(self): raise 'abstract'
    def __str__(self): return self.__str__()

class ParseEmptyFileException(ParseError):
    def __init__(self): pass
    def __str__(self): return _('Your program must have commands.')

class BadCommand(ParseError):
    def __init__(self, token, msg=''):
        self.command = token['statement']
        self.line = token['line']
        self.msg = msg
    def __str__(self):
        return _("Line %i:\n%s") % (self.line+1, self.msg)

class BadIterator(BadCommand):
    def __init__(self, token):
        self.command = token['statement']
        self.line = token['line']
    def __str__(self):
        return _("Line %i:\n%s") % (self.line+1, self.error())
    def error(self):
        return _("Expected positive integer\nGot: %s") % self.command

class IndentError(BadCommand):
    def __init__(self, token):
        self.command = token['statement']
        self.line = token['line']
    def __str__(self):
        return _("Line %i:\n%s") % (self.line+1, self.error())
    def error(self):
        return _("Indentation error")

class ExpectedBlock(BadCommand):
    def __init__(self, line):
        self.line = line
    def __str__(self):
        return _("Line %i:\n%s") % (self.line+1, self.error())
    def error(self):
        return _("Expected code to be indented here")

class LineTooShort(BadCommand):
    def __init__(self, token):
        self.command = token['statement']
        self.line = token['line']
        
    def __str__(self):
        return _("Line %i:\n%s") % (self.line+1, self.error())
    def error(self):
        return _("'%s' statement is incomplete") % self.command

class NoColon(BadCommand):
    def __init__(self, token):
        self.command = token['statement']
        self.line = token['line']
    def __str__(self):
        return _("Line %i:\n%s") % (self.line+1, self.error())
    def error(self):
        return _("Expected '%s' statement to end in ':'") % self.command

class BadStatement(BadCommand):
    def __init__(self, token):
        self.command = token['statement']
        self.line = token['line']
    def __str__(self):
        return _("Line %i:\n%s") % (self.line+1, self.error())
    def error(self):
        return _('"%s" not defined') % (self.command)

class BadTest(BadCommand):
    def __init__(self, token):
        self.command = token['statement']
        self.line = token['line']
    def __str__(self):
        return _("Line %i:\n%s") % (self.line+1, self.error())
    def error(self):
        return _('"%s" is not a valid test') % (self.command)

class BadName(BadCommand):
    def __init__(self, token):
        self.command = token['statement']
        self.line = token['line']
    def __str__(self):
        return _("Line %i:\n%s") % (self.line+1, self.error())
    def error(self):
        return _('"%s" is not a valid name') % (self.command)

class DoubleDefinition(BadCommand):
    def __init__(self, token):
        self.command = token['statement']
        self.line = token['line']
        
    def __str__(self):
        return _("Line %i:\n%s") % (self.line+1, self.error())
    def error(self):
        return _('"%s" has already been defined') % (self.command)
