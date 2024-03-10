#!/usr/bin/env python3
# Generic Compressor, Romaric Duvignau, duvignau@chalmers.se, 01/2018
# Last modified 09/2018

from itertools import tee
from math import ceil

### 2D utils

coeff = lambda i,j: ((j[1]-i[1])/(j[0]-i[0]), (j[0]*i[1]-j[1]*i[0])/(j[0]-i[0]))
coefficients = lambda x0, y0, x1, y1 : ((y1-y0)/(x1-x0), (x1*y0-y1*x0)/(x1-x0))
intersect = lambda x,i,j : ((j[1]-i[1])*x+j[0]*i[1]-j[1]*i[0])/(j[0]-i[0])

DELTA = 0.00001

def intersection(a, b, c, d):
    x1,y1 = a
    x2,y2 = b
    x3,y3 = c
    x4,y4 = d
    d1=(x1*y2-y1*x2)
    d2=(x3*y4-y3*x4)
    d=(x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
    return (d1*(x3-x4)-(x1-x2)*d2)/d, (d1*(y3-y4)-(y1-y2)*d2)/d

### Streaming utils

"""
Stream an input file passed as parameter, and ouput the result of compression
"""
def stream(f, axis, separator=','):
    n = 0
    lastt = None
    for line in f:
        try:
            values = line.split(separator)
            n += 1
            
            if axis > 0:
                #if not lastt or float(values[0]) > lastt:
                yield (float(values[0]), float(values[axis]))
                #lastt = float(values[0])
            else:
                yield (n, float(values[0]))
        
        except ValueError:                          # malformed records
            print("Malformed tuple in file", f, "on line no", n, ":", line)

def streamfile(filename, axis=1, separator=','):
    with open(filename, "r") as f:
        for r in stream(f, axis, separator):
            yield r
            
"""
Stream the timestamps only
"""
def streamtime(f, separator=',', cast=float):
    for line in f:
        yield cast(line.split(separator)[0])

def streamtimefile(filename, separator=',', cast=float):
    with open(filename, "r") as f:
        for line in f:
            yield cast(line.split(separator)[0])

def streamfilelogicaltime(filename, axis, separator=','):
    i = 1
    with open(filename, "r") as f:
        for line in f:
            values = line.split(separator)
            yield i, float(values[axis])
            i += 1
        
def approximatedtimestream(timestream, datastream):
    oldt = None
    for (x,y) in datastream:
        i, t = next(timestream)
        if oldt is not None and t <= oldt:
            yield (oldt+DELTA,y)
        else:
            yield (t,y)
        oldt = t

def logicaltimestream(datastream):
    i = 1
    for t,y in datastream:
        yield (i,y)
        i += 1

def logicaltimes(datastream):
    i = 1
    for record in datastream:
        yield i
        i += 1


### Streaming Compressor Protocols Implementation
            
"""
Template for sequential streaming processor
"""
class StreamCompressor():
    def __init__(self, param='c', bound=255):
        self.parametrize(param, bound)
        self.bound = bound

    def setprotocol(self, protocol):
        self.protocol = protocol

    def parametrize(self, param, bound=255):
        nbbytes = lambda bound : ((bound//2).bit_length())//8+1
        
        if 'n' in param:
            boundbytes = 4
            bound = 4294967295
        elif 'f' in param:
            boundbytes = nbbytes(bound)
        else:
           boundbytes = nbbytes(bound)
        
        if 'o' in param:
            self.protocol = TwoStreamsProtocol(bound, boundbytes)
        elif 'c' in param:
            self.protocol = SingleStreamProtocol(bound, boundbytes)
        elif 'l' in param:
            self.protocol = SingleStreamLidarProtocol(bound, boundbytes)
        else:
            self.protocol = SingleStreamVariantProtocol(bound, boundbytes)


    def compress(self, data, error):
        self.error = error
        yield from self.protocol.compress(self, data)
        
    def reconstruct(self, record, timestream):
        try:
            return self.protocol.reconstruct(record, timestream)
        except StopIteration:
            raise ValueError("given timestream exhausted!")

    def genplastream(self, datastream, error, timestream):
        def databuffered(data, buffer):
            for x in data:
                buffer.append(x)
                yield x
            buffer.append(None)

        buffer = []
        bdata = databuffered(datastream, buffer)
        bL, bm, last_point = [], 0, None
        
        for record in self.compress(bdata, error):
            L, m = self.reconstruct(record, timestream)

            if not buffer: 
                bL.extend(L)
                bm += m
            else:
                if last_point is not None:
                    yield (last_point, (bL, bm))
                
                for x in buffer[:-1]:
                    yield x, None
                    
                last_point = buffer[-1]
                bL, bm = L, m
            
                buffer[:] = []

        yield (last_point, (bL, bm))

    def gendata(self, filename, error=1, axis=1):
        with open(filename, 'r') as f:
            yield from self.genplastream(stream(f, axis), error, streamtime(f))
        
        
"""
Protocols: admits a maximum segment compression length and a weight for
integer values
"""
class Protocol():
    # add minn here
    def __init__(self, maxn, inputsize=8, outputsize=8, singletons=True):
        self.maxn = maxn
        self.inputsize = inputsize # in bytes
        self.cntsize = int(ceil(maxn.bit_length() / 8)) # n in line segments
        ## can use float here, 4 bytes only? then garentee breaks slightly
        self.coeffsize = outputsize # for (a,b)-coefficients in line segments
        self.singletons = singletons

    def cost(self, nbbytes):
        return nbbytes/self.inputsize

"""
Abstract Class: process a data stream of (x,y) tuples and generate a compressed stream
of singleton point (y,) or approximation segments (x,n,a,b)
"""
class TwoStreamsProtocol(Protocol):
    
    def compress(self, streamCompressor, data):
        x0 = x1 = x2 = None                             # To handle <3 streams
        try:
            x0, y0 = next(data)
            x1, y1 = next(data)
            x2, y2 = next(data)
            L = []
            
            while True:                                 # Initialization                
                streamCompressor.initialize(x0,y0,x1,y1)

                if streamCompressor.check(x2,y2) :      # n >= 3 ?
                    L.append(y0)
                    x0, y0 = x1, y1
                    x1, y1 = x2, y2
                    x2, y2 = next(data)
                    continue
                
                streamCompressor.update(x2,y2)
                
                n = 3
                while True:                             # Line construction
                    x, y = next(data)

                    # Check if (x,y) within the limit slopes: terminate line ?
                    if n >= self.maxn or streamCompressor.check(x,y) :
                        if self.singletons and n < 4 :  # Flush 1 isolated point
                            L.append(y0)
                            x0, y0 = x1, y1
                            x1, y1 = x2, y2
                            x2, y2 = x, y
                        else :                          # Flush one segment
                            a, b = streamCompressor.flush()
                            yield L, (x0, n, a, b)
                            L = []
                            x0, y0 = x, y
                            x1, y1 = next(data)
                            x2, y2 = next(data)
                        break

                    streamCompressor.update(x,y)
                    n += 1

        except StopIteration:                           # Generator dried out
            if x0 is not None:
                if x1 is None or x1 <= x0:
                    yield L+[y0], None
                elif x2 is None or x2 <= x1:
                    yield L+[y0, y1], None
                elif n < 4:
                    yield L+[y0, y1, y2], None
                else:
                    a, b = streamCompressor.flush()
                    yield L, (x0, n, a, b)

    def reconstruct(self, record, time):
        reconstructed = []
        L, segment = record
        m = len(L)
        
        for y in L:
            x = next(time)
            reconstructed.append((x,y))

        if segment is not None:
            x0, n, a, b = segment
            m += self.cost(self.inputsize + self.cntsize + 2*self.coeffsize)

            for i in range(n):
                x = next(time)
                reconstructed.append((x,a*x+b))
                
        return (reconstructed, m)
    
"""
Abstract Class: process a data stream of (x,y) tuples and generate a compressed
stream of singleton point (1,y) or approximation segment triplets (n,a,b)
"""
class SingleStreamProtocol(Protocol):

    def compress(self, streamCompressor, data):
        minpoints = int(ceil((self.coeffsize*2+self.cntsize) / self.inputsize))
        buffersize = minpoints-1
        pointbuffer = [None]*buffersize                 # To handle <min streams
        try:
            x0, y0 = next(data)
            x1, y1 = next(data)
            #for _ 
            while True:                                 # Initialization
                n = 2
                streamCompressor.initialize(x0,y0,x1,y1)
                
                while True:                             # Line construction
                    x, y = next(data)

                    # Check if (x,y) is within the limit slopes: terminate line ?
                    if n >= self.maxn or streamCompressor.check(x,y) :
                        if self.singletons and n == 2 : # Flush 1 isolated point
                            yield (1, y0)
                            x0, y0 = x1, y1
                            x1, y1 = x, y
                        else :                          # Flush one segment
                            a, b = streamCompressor.flush()
                            yield (n, a, b)
                            x0, y0 = x, y
                            x1, y1 = next(data)
                        break

                    streamCompressor.update(x,y)
                    n += 1

        except StopIteration:                           # Generator dried out
            if x0 is not None:
                if x1 is None or x1 < x0:
                    yield (1, y0)
                else:
                    a, b = streamCompressor.flush()
                    yield n, a, b

    def reconstruct(self, record, time):
        if record[0] == 1:
            x = next(time)
            return ([(x,record[1])], self.cost(self.cntsize+self.inputsize))

        n, a, b = record
        reconstructed = []
        
        for i in range(n):
            x = next(time)
            reconstructed.append((x,a*x+b))
            
        return (reconstructed, self.cost(self.cntsize + 2*self.coeffsize))

class SingleStreamLidarProtocol(Protocol):
    def compress(self, streamCompressor, data):
        protocol = SingleStreamProtocol(self.maxn, self.inputsize)
        for record in protocol.compress(streamCompressor, data):
            if record[0] > 1 and record[1] == 0:
                yield (-record[0], record[2])
            else:
                yield record

    def reconstruct(self, record, time):
        if record[0] == 1:
            return ([(next(time),record[1])],
                    self.cost(self.cntsize + self.inputsize))

        if record[0] < 0:
            n, a, b = -record[0], 0, record[1]
            weight = self.cost(self.cntsize + self.coeffsize)
        else:
            n, a, b = record
            weight = self.cost(self.cntsize + 2*self.coeffsize)
            
        return ([(t,a*t+b) for t in (next(time) for _ in range(n))], weight)
        
"""
Abstract Class: process a data stream of (x,y) tuples and generate a compressed
stream of singleton tuples (-m,y0,...,ym) or approx segment triplets (n,a,b)
"""
class SingleStreamVariantProtocol(Protocol):
    def compress(self, streamCompressor, data):
        x0 = x1 = None                                  # To handle <2 streams
        try:
            x0, y0 = next(data)
            x1, y1 = next(data)
            L = []
            
            while True:                                 # Initialization
                n = 2
                streamCompressor.initialize(x0,y0,x1,y1)
                
                while True:                             # Line construction
                    x, y = next(data)

                    # Check if (x,y) within the limit slopes: terminate line ?
                    if n >= self.maxn or streamCompressor.check(x,y) :
                        if self.singletons and n == 2 : # Flush 1 isolated point
                            L += [y0]
                            if len(L) == self.maxn:
                                yield tuple([-len(L)]+L)
                                L = []
                            x0, y0 = x1, y1
                            x1, y1 = x, y
                        else :                          # Flush one segment
                            a, b = streamCompressor.flush()
                            if L:
                                yield tuple([-len(L)]+L)
                                L = []
                            yield n, a, b
                            x0, y0 = x, y
                            x1, y1 = next(data)
                        break

                    streamCompressor.update(x,y)
                    n += 1

        except StopIteration:                           # Generator dried out
            if x0 is not None:
                if x1 is None or x1 < x0:
                    L += [y0]
                    yield tuple([-len(L)]+L)
                else:
                    if L:
                        yield tuple([-len(L)]+L)
                    a, b = streamCompressor.flush()
                    yield n, a, b

    def reconstruct(self, record, time):
        reconstructed = []
        
        if record[0] < 0:
            n = abs(record[0])
            for i in range(n):
                x = next(time)
                reconstructed.append((x,record[i+1]))
            return (reconstructed, self.cost(self.cntsize + n*self.inputsize))

        n, a, b = record
        for i in range(n):
            x = next(time)
            reconstructed.append((x,a*x+b))
            
        return (reconstructed, self.cost(self.cntsize + 2*self.coeffsize))
