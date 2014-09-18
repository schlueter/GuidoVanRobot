'''
Stepper.step steps through one instruction of a GvR program
at a time, and then it calls back into your world 
object to actually do MOVE(), TURNLEFT(), etc.

Read TESTstepper.py to grok this.
'''
import translate,sys

class OutOfInstructionsException(Exception): 
    def __str__(self): return 'Out of instructions'
class InfiniteLoopException(Exception):
    pass

class StackFrame:
    def __init__(self, block):
        self.whichStatement = -1
        self.block = block
    def nextLineOfCode(self, world):
        self.whichStatement += 1
        if self.whichStatement < len(self.block.statements):
            return self.block.statements[self.whichStatement]

def currLine(obj):
    curr = obj.block.statements[obj.whichStatement]
    if getBlockFrame(curr):
        return ''
    else:
        lnum = str(curr.line+1).rjust(3)
        stat = str(curr.statement)
        return '  '+lnum+'    '+stat+'\n'

def atEndOfBlock(obj):
    return obj.whichStatement >= len(obj.block.statements)
def atNewBlock(obj):
    return obj.whichStatement == 0
def checkCondition(obj, world):
    methodInWorldClass = getattr(world, obj.condition.statement)
    return methodInWorldClass()
def getBlockFrame(block):
    blockFrames = {
        'DoLoop': DoLoop,
        'WhileLoop': WhileLoop,
        'IfStatement': IfStatement
    }
    return blockFrames.get(block.__class__.__name__,None)

class DoLoop:
    def __init__(self, doLoop):
        self.whichLoop = 0
        self.whichStatement = -1
        self.block = doLoop.block
        self.iterations = int(doLoop.iterator)
    def nextLineOfCode(self, world):
        self.whichStatement += 1
        if atEndOfBlock(self):
            self.whichStatement = 0
            self.whichLoop += 1
        if self.whichLoop < self.iterations:
            return self.block.statements[self.whichStatement]
    
class WhileLoop:
    def __init__(self, whileLoop):
        self.whichStatement = -1
        self.block = whileLoop.block
        self.whileLoop = whileLoop
    def nextLineOfCode(self, world):
        self.whichStatement += 1
        if atEndOfBlock(self):
            self.whichStatement = 0
        if atNewBlock(self):
            if not checkCondition(self.whileLoop, world): return
        return self.block.statements[self.whichStatement]

class IfStatement:
    def __init__(self, ifStatement):
        self.whichStatement = -1
        self.ifStatement = ifStatement
        self.conditionalBlocks = [ifStatement] + ifStatement.elifs
        self.block = None
    def nextLineOfCode(self, world):
        self.whichStatement += 1
        if atNewBlock(self):
            for conditionalBlock in self.conditionalBlocks:
                if checkCondition(conditionalBlock, world):
                    self.block = conditionalBlock.block
                    break
            if not self.block:
                if self.ifStatement.elseObj:
                    self.block = self.ifStatement.elseObj
                else:
                    return
        if atEndOfBlock(self):
            return
        return self.block.statements[self.whichStatement]

class Stepper:
    def __init__(self, gvr, world, debugger=None):
        tree = translate.gvrToSyntaxTree(gvr)
        self.world = world
        self.stack = [StackFrame(tree.block)]
        self.funcs = {}
        for func in tree.functions:
            self.funcs[func.name] = func
        self.debugger = debugger
        self.infinite_count = 0
    def step(self):
        self.infinite_count +=1
        if self.infinite_count > 9586:
            v = self.infinite_count
            self.infinite_count = 0
            raise InfiniteLoopException,v
        lineOfCode = self.nextLineOfCode()
        blockFrame = getBlockFrame(lineOfCode)
        if blockFrame:
            self.enterBlock(blockFrame(lineOfCode))
            return
        command = lineOfCode.statement
        if self.funcs.has_key(command):
            self.enterUserDefinedMethod(command)
            return
        if self.debugger:
            self.debugger.setLine(lineOfCode.line)
        if lineOfCode.__class__.__name__ == 'Cheat':
            self.world.cheat(lineOfCode.statement)
        else:
            self.doPrimitive(command)
    def doPrimitive(self, command):
        methodInWorldClass = getattr(self.world, command.upper())
        methodInWorldClass()
    def enterBlock(self, stackFrame):
        self.stack.append(stackFrame)
        self.step()
    def enterUserDefinedMethod(self, command):
        self.enterBlock(StackFrame(self.funcs[command].block))
    def stackTrace(self):
        trace = 'Line     Statement\n'
        for frame in self.stack:
            trace += currLine(frame)
        return trace
    def nextLineOfCode(self):
        if len(self.stack):
            lineOfCode = self.stack[-1].nextLineOfCode(self.world)
            if lineOfCode:
                return lineOfCode
            else:
                self.stack.pop()
                return self.nextLineOfCode()
        else: raise OutOfInstructionsException
