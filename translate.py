# see INFO for license
import build
import gvrparser
import re

def stripComments(program):
    return [line.split("#")[0].replace(':', ' : ') for line in program.splitlines()]
    
def getTokens(lines):
    return [ {
                'statement' : word, 
                'line' : idx,
                'indent': len(lines[idx])-len(lines[idx].lstrip())
                } for idx in range(len(lines)) for word in lines[idx].split()
              ]
            
def gvrToSyntaxTree(gvr):
    if not re.search('\S', gvr): 
        raise gvrparser.ParseEmptyFileException()
    return gvrparser.parseProgram(getTokens(stripComments(gvr)))
    
def gvrToPython(gvr):
    return build.buildProgram(gvrToSyntaxTree(gvr))
