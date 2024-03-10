#!/usr/bin/env python3
# Angle Compressor, Romaric Duvignau, duvignau@chalmers.se, 11/2017
# Last modified 09/2018

from compressor import *

"""
Process a data stream of (x,y) tuples and generate a compressed stream by
keeping track of the angle of possible lines from an initial point
"""
class AngleCompressor(StreamCompressor):
    def initialize(self,x0,y0,x1,y1):
        a, b, c, d = (x0, y0-self.error), (x1, y1+self.error), \
                     (x0, y0+self.error), (x1, y1-self.error)
        self.i, self.j = intersection(a,b,c,d)
        self.slope = lambda x, y : (y-self.j)/(x-self.i)
        self.amin, self.amax = self.slope(x1, y1-self.error), \
                               self.slope(x1, y1+self.error)

    def check(self,x,y):
        return self.amin*x+self.j-self.amin*self.i > y+self.error or \
               self.amax*x+self.j-self.amax*self.i < y-self.error

    def flush(self):
        return ((self.amin+self.amax)/2, self.j-(self.amin+self.amax)*self.i/2)

    def update(self,x,y):
        self.amin, self.amax = max(self.amin, self.slope(x,y-self.error)), \
                                   min(self.amax, self.slope(x,y+self.error))

def makecompressorAngle():
    return AngleCompressor()


# MAIN: File streaming part, process a single file or directory
if __name__ == "__main__":
    from plastats import processfile
    processfile(makecompressorAngle)
