import sys,os
try:
    logpath = os.path.join(os.environ["HOMEDRIVE"],os.environ["HOMEPATH"])
except:
    # for win 98
    logpath = os.environ["TEMP"]
    
class StdoutCatcher:
    def __init__(self):
        self.pyoutf = os.path.join(logpath,"gvr_stdout.log")
        f = open(self.pyoutf,'w')
        f.close()    
    def write(self, msg):
        self.outfile = open(self.pyoutf, 'a')
        self.outfile.write(msg)
        self.outfile.close()
    def flush(self):
        return None        

class StderrCatcher:
    def __init__(self):
        self.pyerrf = os.path.join(logpath,"gvr_stderr.log")
        f = open(self.pyerrf,'w')
        f.close()    
    def write(self, msg):
        self.outfile = open(self.pyerrf, 'a')
        self.outfile.write(msg)
        self.outfile.close()
    def flush(self):
        return None        

sys.stdout = StdoutCatcher()
sys.stderr = StderrCatcher()
