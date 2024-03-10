#!/usr/bin/env python3
# Convex Hull Compressor, Romaric Duvignau, duvignau@chalmers.se, 2018
# Last modified 09/2018

from compressor import *
from bisect import bisect_left as binsearch

### Convex Hull utils

class ProjectedList():
    def __init__(self, convexhull, x):
        self.list = convexhull.hull
        self.d = convexhull.d
        self.axis = x

    def __len__(self):
        return len(self.list)-1
    
    def __getitem__(self, i):
        return self.d*intersect(self.axis, self.list[i], self.list[i+1])
    
class ConvexHull():        
    def __init__(self, x0, y0, x1, y1, error, up):
        self.d = -1 if up else 1
        self.hull = [(x0,y0+self.d*error), (x1,y1+self.d*error)]

    def __getitem__(self, i):
        return self.hull[i]

    def index(self, x, y):
        return binsearch(ProjectedList(self, x), y*self.d)
    
    def update_head(self,x,y):
        i = self.index(x, y)
        if i != 0:
            y0 = intersect(self.hull[0][0], self.hull[i], (x,y))
            self.hull[:i] = [(self.hull[0][0],y0)]

    def update_tail(self,x,y):
        self.hull[self.index(x, y)+1:] = [(x,y)]

"""
Process a data stream of (x,y) tuples and generate a compressed stream by
maintaining two convex hulls (lower and upper) of the error endpoints
"""
class ConvexhullCompressor(StreamCompressor):
    def initialize(self,x0,y0,x1,y1):
        self.ymin, self.ymax, self.t = y1-self.error, y1+self.error, x1
        self.lowerhull = ConvexHull(x0,y0,x1,y1,self.error,up=True)
        self.upperhull = ConvexHull(x0,y0,x1,y1,self.error,up=False)

    def check(self,x,y):
        self.newymin = intersect(x, self.upperhull[0], (self.t,self.ymin))
        self.newymax = intersect(x, self.lowerhull[0], (self.t,self.ymax))
        return y-self.error > self.newymax or y+self.error < self.newymin

    def flush(self):
        ystart = (self.lowerhull[0][1]+self.upperhull[0][1])/2
        yend = (self.ymin+self.ymax)/2
        return coefficients(self.lowerhull[0][0], ystart, self.t, yend)

    def update(self,x,y):
        self.ymin, self.ymax, self.t = self.newymin, self.newymax, x

        if y-self.error > self.ymin :
            self.ymin = y-self.error
            self.upperhull.update_head(x,self.ymin)
            
        if y+self.error < self.ymax :
            self.ymax = y+self.error
            self.lowerhull.update_head(x,self.ymax)

        self.lowerhull.update_tail(x,y-self.error)
        self.upperhull.update_tail(x,y+self.error)


# MAIN: File streaming part, process a single file
if __name__ == "__main__":
    from plastats import processfile
    processfile(lambda : ConvexhullCompressor())
