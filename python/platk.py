#!/usr/bin/env python3
# Python PLA Stream Compressor, Romaric Duvignau, duvignau@chalmers.se, 2018
# Last update Sept-2018

from os import listdir
from os.path import isdir, join, splitext

from itertools import tee
from math import sqrt
from random import random, gauss
from compressor import *

### old-interface fix ###

def gentimestamps(data):
    for t,y in data:
        yield t

def genvalues(data):
    for t,y in data:
        yield y

def genrecords(compressor, datastream, maxerror):
    data1, data2 = tee(datastream)
    for r in compressor.genplastream(data1, maxerror, gentimestamps(data2)):
        yield r

### generators ###

def genreconstructed(compressor, datastream, maxerror):
    for (point,R) in genrecords(compressor, datastream, maxerror):
        if R is not None:
            for (x,y) in R[0]:
                yield (x,y)
    
def generrors(compressor, datastream, maxerror):
    original_stream, copy_stream = tee(datastream)
    for (x,y) in genreconstructed(compressor, copy_stream, maxerror):
        xorig, yorig = next(original_stream)
        yield abs(y-yorig)
        
def gendelays(compressor, datastream, maxerror):
    n = m = 0
    for (point,R) in genrecords(compressor, datastream, maxerror):
        n += 1
        if R is not None:
            for (x,y) in R[0]:
                m += 1
                yield (n-m)

## 3d error and delays

def genderrors(compressor, datastreams, maxerrors):
    gen = [generrors(compressor, datastreams[i], maxerrors[i])
           for i in range(len(datastreams))]
    try:
        while True:
            yield sqrt(sum([next(gen[i])**2 for i in range(len(datastreams))]))
    except StopIteration:
        pass
    
def genddelays(compressors, datastreams, maxerrors):
    gen = [gendelays(compressors[i], datastreams[i], maxerrors[i])
           for i in range(len(datastreams))]
    try:
        while True:
            yield [next(gen[i]) for i in range(len(datastreams))]
    except StopIteration:
        pass

### lists ###

def reconstructedlist(compressor, filename, axes, maxerror):
    n = m = 0
    datastream = streamfile(filename, axis)
    def genlist():
        nonlocal n, m
        for (point,R) in genrecords(compressor, datastream, maxerror):
            n += 1
            if R is not None:
                m += R[1]
                for (x,y) in R[0]:
                    yield y
    return list(genlist()), m/n



### save to file ###

from linear import LinearCompressor

def reconstruct0(filename, axes=[1], maxerrors=[1], types=None, ext='x', sep=','):
    n = m = e = 0
    compr = LinearCompressor()
    compr.setprotocol(SingleStreamProtocol(255, 0.125))

    def genrec(axis, error, typ):
        nonlocal n, m, e
        datastream1, datastream2 = tee(streamfile(filename, axis))
        for (point,R) in genrecords(compr, datastream1, error):
            if R is not None:
                m += R[1]
                for (x,y) in R[0]:
                    n += 1
                    x0, y0 = next(datastream2)
                    if typ:
                        y = round(y) if typ is int else typ(y)
                    e += abs(y-y0)
                    yield y

    with open(filename, "r") as f:
        with open(filename+ext, "w") as outf:
            typs = [None]*len(axes) if not types else types
            genrecs = [genrec(axes[i],maxerrors[i],typs[i])
                       for i in range(len(axes))]
                
            for line in f:
                record = line.strip().split(sep)
                for i in range(len(axes)):
                    record[axes[i]] = str(next(genrecs[i]))
                print(sep.join(record), file=outf)
            
    return m, e, n

def reconstruct(filename, axes=[1], maxerrors=[1], types=None, ext='x', sep=','):
    return reconstruct0(filename,axis,maxerrors,types,ext,sep)

def reconstructfiles(files, axes=[1], maxerrors=[1], types=None, ext='x', sep=','):
    m = e = n = 0
    for file in files:
        ml, el, nl = reconstruct0(file,axes,maxerrors,types,ext,sep)
        m += ml
        e += el
        n += nl
    return m/n, e/n

def savereconstructed(compressor, datastream, maxerror, outputfilename):
    with open(outputfilename, "w") as f:
        for (x,y) in genreconstructed(compressor, datastream, maxerror):
            print(x, "{0:.3f}".format(y), sep=",", file=f)

def savereconstructeddir(compressor, directory, axes, maxerrors):
    n = m = 0
    for filename in [join(directory, file) for file in listdir(directory)
                     if file.endswith('.csv')]:
        with open(splitext(filename)[0]+"_"+str(maxerrors)+".csvz", "w") as f:
            with open(filename, "r") as file:
                #print(filename)

                def genrecfunc(axis, maxerror):
                    nonlocal m
                    for (point,R) in genrecords(compressor,
                        streamfile(filename, axis), maxerror):
                        if R is not None:
                            m += R[1]
                            for (x,y) in R[0]:
                                yield y

                genrec = {}
                i = 0
                for axis in axes:
                    genrec[axis] = genrecfunc(axis, maxerrors[i])
                    i += 1
                    
                for line in file:
                    record = line.split(",")
                    n += 2
                    for axis in axes:
                        record[axis] = next(genrec[axis])
                        
                    print(",".join(str(value).strip() for value in record), file=f)
    return m/n
### synthetic data ###

def gensynthetic(length,alpha=0.1,beta=0.2,gamma=0.2,delta=0.01,epsilon=0.66):
    x = speed = 0
    on = True
    turn = False
    for t in range(length):
        if on:
            if random() > alpha:
                yield (t, x)
            else:
                on = False
        elif random() > beta:
            on = True

        if turn:
            if random() < gamma:
                turn = False

            speed *= epsilon
        else:
            if random() < delta:
                turn = True

            speed += gauss(0,1)

        x += speed

