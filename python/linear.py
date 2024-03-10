#!/usr/bin/env python3
# Linear Regression Compressor, Romaric Duvignau, duvignau@chalmers.se, 2018
# Last modified 09/2018

from compressor import *

DELTA = 0.0000000001

"""
Process a data stream of (x,y) tuples and generate a compressed stream by
computing the best-fit line and test if all errors are within the threshold
"""
class LinearCompressor(StreamCompressor):
    def initialize(self,x0,y0,x1,y1):
        self.sumx = x0+x1
        self.sumy = y0+y1
        self.sumx2 = x0*x0+x1*x1
        self.sumxy = x0*y0+x1*y1
        self.a, self.b = coefficients(x0, y0, x1, y1)
        self.uhull = [(x0,y0+self.error), (x1,y1+self.error)]
        self.lhull = [(x0,y0-self.error), (x1,y1-self.error)]
        self.n = 2

    def check(self,x,y):
        self.sumx += x
        self.sumy += y
        self.sumx2 += x*x
        self.sumxy += x*y
        self.n += 1

        self.newa = (self.n*self.sumxy-self.sumx*self.sumy) \
                   /(self.n*self.sumx2-self.sumx*self.sumx)
        self.newb = (self.sumy-self.newa*self.sumx)/self.n

        if not (y-self.error-0.0000000001 <= x*self.newa+self.newb <= y+self.error+0.0000000001):
            return True
        
        # Linear checking for now, nothing smarter
        for x, y in self.uhull:
            if self.newa*x+self.newb > y+0.0000000001:
                return True
            
        for x, y in self.lhull:
            if self.newa*x+self.newb < y-0.0000000001:
                return True

        return False

    def flush(self):
        return self.a, self.b

    def update(self,x,y):
        self.a, self.b = self.newa, self.newb

        # Update Hulls
        while len(self.uhull)>2 and \
              intersect(x,self.uhull[-2],self.uhull[-1]) > y+self.error:
            del self.uhull[-1]
        self.uhull.append((x,y+self.error))
        
        while len(self.lhull)>2 and \
              intersect(x,self.lhull[-2],self.lhull[-1]) < y-self.error:
            del self.lhull[-1]
        self.lhull.append((x,y-self.error))

def makecompressorlinear():
    return LinearCompressor()

# MAIN: File streaming part, process a single file or directory
if __name__ == "__main__":
    from plastats import processfile
    processfile(makecompressorlinear)
