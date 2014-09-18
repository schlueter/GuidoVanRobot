# read INFO for licensing information

import re
from gvrparser import TESTS, COMMANDS
def PySyntax(str):
    if str in TESTS or str in COMMANDS:
        return re.sub("_", "_", str).upper()
    else:
        return str

def build(obj, indent=''): 
    return eval('build'+obj.__class__.__name__+'(obj,indent)')

def buildStatement(self, indent):
    return "%sself.%s(%i)\n" % (indent, PySyntax(self.statement), self.line)

def buildCheat(self, indent):
    return "%sself.cheat('%s', %i)\n" % (indent, PySyntax(self.statement), self.line)

def buildTestCondition(self, indent=''):
    return "self.%s(%i)" % (PySyntax(self.statement), self.line)

def buildIfStatement(self, indent):
    code = "%sif %s:\n%s" % (indent, 
                             buildTestCondition(self.condition), 
                             build(self.block, indent+'  '))
    for elifObj in self.elifs: code += buildElifStatement(elifObj, indent)
    if self.elseObj: code += buildElseStatement(self.elseObj, indent)
    return code

def buildElseStatement(self, indent):
    return "%selse:\n%s" % (indent,
                            build(self, indent+ '  '))

def buildElifStatement(self, indent):
    return "%selif %s:\n%s" % (indent,
                             buildTestCondition(self.condition), 
                             build(self.block, indent+'  '))


def buildWhileLoop(self, indent):
    return "%swhile %s:\n%s" % (indent,
                                buildTestCondition(self.condition),
                                build(self.block, indent+'  '))

def buildDoLoop(self, indent):
    return "%sfor i in range(%s):\n%s" % (indent,
                                          self.iterator,
                                          build(self.block, indent+'  '))
def buildBlock(self, indent=''):
    code = ""
    for statement in self.statements:
        code += build(statement, indent)
    return code

def buildDefine(self, indent=''):
    return '''\
%sdef %s(self, line):
%s  self._enter('%s', line)
%s%s  self._exit()
''' % (
    indent, self.name,
    indent, self.name,
    build(self.block, indent+'  '), indent)

def buildProgram(self, indent=''):
    definitions = ""
    for func in self.functions:
        definitions += build(func, indent+'  ')
    return "class StudentRobot(Robot):\n%s  def execute(self):\n%s" % (definitions, build(self.block, indent+'  '+'  '))
