#!/usr/bin/env python3
# Python PLA Stream Compressor, Romaric Duvignau, duvignau@chalmers.se, 2018
# Last update Sept-2018

## cleaning update -- June 2020

import struct
from math import sqrt
from collections import defaultdict
import argparse
from os import listdir
from os.path import isdir, join
from sys import argv

from compressor import *
from platk import *

DELTA = 0.0001

#def approximatets(compressor, filename, errors):

def plastats(originalstream, gendatastream, maxerror, deltatime,
             verbose=False, sep=","):
    nb_original = errors = merror = sumerror2 = nb_values = 0
    n = delays = discarded = 0
        
    #try:
    for (point,R) in gendatastream:
        #print(point,R)
        n += 1
        if R is not None:
            L, m = R
            nb_values += m
            
            for (x,y) in L:
                
                xorig, yorig = next(originalstream)

                nb_original += 1
                error = abs(y-yorig)

                merror = max(merror,error)
                delays += (n-nb_original)
                
                # Check for bugs in invoked method and discard if found
                if error > maxerror+DELTA or abs(xorig-x) > deltatime+DELTA:
                    if verbose and abs(xorig-x) > deltatime+DELTA:
                        print("BUG: reconstructed timestamp", x, "expected", xorig)
                    if verbose and error > maxerror+DELTA:
                        print("BUG: expected", xorig, yorig, \
                              "got", x, y, "error", yorig-y)
                    discarded += 1

                #else:
                sumerror2 += error*error
                errors += error
                
                
                
    #except StopIteration:
    #    if verbose:
    #        print("BUG: too many reconstructed tuples!")

    
    for x, y in originalstream:                    # End of file uncompressed ?
        if verbose:
            print("BUG:", x, y, " has not been reconstructed!")
        discarded += 1

    nb_original = 1 if nb_original == 0 else nb_original

    stats = {}
    stats['m'] = nb_values
    stats['n'] = nb_original
    stats['x'] = merror
    stats['s'] = sumerror2
    stats['d'] = delays
    stats['e'] = errors
    stats['i'] = discarded

    return stats

def printstats(stats):
    print("Nb records\t", stats['n'])
    print("Avg compr.\t", stats['m']/stats['n'])
    print("Avg error\t", stats['e']/stats['n'])
    print("RMS error\t", sqrt(stats['s']/stats['n']))
    print("Max error\t", stats['x'])
    print("Avg delay\t", stats['d']/stats['n'])
    print("Avg discarded\t", stats['i']/stats['n'])

def printstatsall(stats,errors):
    lines = ["Column (err)\t", "No records\t", "Avg compr. %\t",
             "Avg error\t", "RMS error\t",
             "Max error\t", "Avg delay\t", "Avg disc. %\t"]
    myformati = lambda i : "|"+'{:10}'.format(i)
    myformatf = lambda f : "|"+'{:10.3f}'.format(f)

    def add_column_stat(stats):
        lines[1] += myformati(stats['n'])
        lines[2] += myformatf(100*stats['m']/stats['n'])
        lines[3] += myformatf(stats['e']/stats['n'])
        lines[4] += myformatf(sqrt(stats['s']/stats['n']))
        lines[5] += myformatf(stats['x'])
        lines[6] += myformatf(stats['d']/stats['n'])
        lines[7] += myformatf(100*stats['i']/stats['n'])

    if stats['n'] == 0:
        #print("Empty directory")
        return

    for i in range(len(errors)):
        if errors[i] >= 0:
            lines[0] += "|"+'{:1} ({:6})'.format(i, errors[i])
            add_column_stat(stats[i])

    if len([err for err in errors if err>=0]) > 1:
        lines[0] += "|    "+'OVERALL'
        add_column_stat(stats)   
            
    print("\n".join(lines))
        
# errors is a list of error for each axis, -1 disactivate PLA on that axis 
def plastatsdir(files, compressors, errors, timestamps=0, verb=False, perfile=False, sep=","):
    stats = defaultdict(int)
    axes = list(i for i in range(len(errors)) if errors[i] >= 0)
    deltatime = max(errors[0],0)
    
    for i in axes:
        stats[i] = defaultdict(int)
    
    for filename in files:
        for i in axes:
            if verb and perfile:
                print("processing", filename, "column", i)
                print("-"*80)

            filestrm1, filestrm2 = tee(streamfile(filename, i, sep))
            
            if i == 0:
                timedstream, time2 = tee(filestrm1)
                gendatastrm = compressors[i].genplastream(timedstream, errors[i], gentimestamps(time2))
            else:
                if timestamps == 1:
                    timedstream = logicaltimestream(filestrm1)
                    deltatime = float('inf')
                    time1, time2 = tee(timedstream)
                    gendatastrm = compressors[i].genplastream(time1, errors[i], gentimestamps(time2))
            
                else:
                    
                    if errors[0] < 0:
                        gentimes = streamfile(filename, 0, sep)
                    else:
                        gentimes = genreconstructed(compressors[0],
                                    streamfile(filename, 0, sep), errors[0])

                    if timestamps == 2:
                        gendatastrm = compressors[i].genplastream(filestrm1, errors[i], genvalues(gentimes))
            
                    else:
                        time1, time2 = tee(gentimes)
                        timedstream = approximatedtimestream(time1, filestrm1)
                        gendatastrm = compressors[i].genplastream(timedstream, errors[i], genvalues(time2))
            
            stats[i][filename] = plastats(filestrm2, gendatastrm, errors[i],
                                          deltatime, verb, sep)

        for i in axes:        
            for v in "mnsdei":
                stats[i][v] += stats[i][filename][v]
                stats[v] += stats[i][filename][v] 
            stats['x'] = max(stats['x'], stats[i][filename]['x'])
            stats[i]['x'] = max(stats[i]['x'], stats[i][filename]['x'])

            if perfile:
                printstats(stats[i][filename])
                print("-"*80)

    return stats
    
def processfile(makecompressor):
    parser = argparse.ArgumentParser(description="""
                Compute different PLA statistics using by default
                the single stream protocol.""")
    parser.add_argument("target",
                        help="either a single file or a directory to process")
    parser.add_argument("errors", nargs='+', type=float,
                        help="""list of maximum tolerated errors for PLA compr.
    for each channel; negative value= turn off PLA on that channel""")
    
    parser.add_argument("-c", "--compression", action="store_true",
                        help="output only average compression")
    parser.add_argument("-e", "--avgerror", action="store_true",
                        help="output only average error")
    parser.add_argument("-Q", "--rmserror", action="store_true",
                        help="output only rms error")
    parser.add_argument("-m", "--maxerror", action="store_true",
                        help="output only max error")
    parser.add_argument("-d", "--delay", action="store_true",
                        help="output only average delay")
    parser.add_argument("-i", "--discarded", action="store_true",
                        help="output only average discarded tuples")

    protocolgroup = parser.add_mutually_exclusive_group()
    protocolgroup.add_argument("-I", "--twostream", action="store_true",
                        help="set 2 streams protocol")
    protocolgroup.add_argument("-II", "--singlestreamv", action="store_true",
                        help="set single stream variant protocol")
    protocolgroup.add_argument("-III", "--lidarvariant", action="store_true",
                        help="set single stream lidar variant protocol")

    parser.add_argument("-b", "--bnd", default=255, type=int, 
                        help="""set segment length bound; default=256;
                        this bound also determines the number of bytes used to
                        encode the counter parameter in pla records""")

    parser.add_argument("-t", "--inputsize", default=8, type=int,
                        help="""set input size in bytes; default=8;
                        """)

    parser.add_argument("-o", "--outputsize", default=8, type=int,
                        help="""set output size in bytes (for alpha/beta);
                        default=8; """)

    parser.add_argument("-S", "--singleoff", help="turn off singleton values",
                        action="store_true")

    parser.add_argument("-l", "--logicaltimes", help="""uses logical timestamps for all
                        fields (default use channel 0 as time channel)""",
                        action="store_true")
    parser.add_argument("-a", "--realtimes", help="""uses real timestamps for all
                        fields as input (default use approximated channel 0)""",
                        action="store_true")

    parser.add_argument("-x", "--zip", action="store_true",
                        help="""outputs pla compression records""")
    parser.add_argument("-n", "--endpoints", action="store_true",
                        help="""outputs pla segments' endpoints + singletons""")
    
    parser.add_argument("-r", "--reconstruct", action="store_true",
                        help="""outputs reconstructed values""")
    parser.add_argument("-D", "--ndelays", action="store_true",
                        help="""outputs average max delays (multi-dim. delays)""")
    
    parser.add_argument("-s", "--sep", default=',',
                        help="set datafile column sep; default=','")
    parser.add_argument("-p", "--perfile", help="""if target is a directory,
                        print statistics for each processed file""",
                        action="store_true")
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")
    parser.add_argument("-q", "--quiet", help="turn off output",
                        action="store_true")

    args = parser.parse_args()
    
    errors = args.errors
    
    if args.twostream:
        protocol = TwoStreamsProtocol
    elif args.singlestreamv:
        protocol =  SingleStreamVariantProtocol
    elif args.lidarvariant:
        protocol =  SingleStreamLidarProtocol
    else:
        protocol =  SingleStreamProtocol

    compressors = [makecompressor() for e in errors]
    for i in range(len(errors)):
        compressors[i].setprotocol(
            protocol(args.bnd, args.inputsize, args.outputsize,
                     not args.singleoff)) 

    if isdir(args.target):
        files = [join(args.target, file) for file in listdir(args.target)
                 if file.endswith('.csv')]
    else:
        files = [args.target]

    if args.zip:
        for filename in files:
            for i in range(len(errors)):
                if errors[i] != -1:
                    data = logicaltimestream(streamfile(filename,i,args.sep))
                    if args.verbose:
                        print(filename, "axis", i, "maxerror", errors[i])
                    for record in compressors[i].compress(data, errors[i]):
                        if len(record) == 3:
                            print(record[0],record[1],record[2],sep=args.sep)
                        else:
                            print(record[0],record[1],sep=args.sep)
        return

    if args.ndelays:
        nbtuples = muldimdelaysum = 0
        delaysums = [0]*len(errors)
        
        for filename in files:
            datastreams = [streamfilelogicaltime(filename,i) for i in range(len(errors))]

            for delays in genddelays(compressors, datastreams, errors):
                nbtuples += 1
                for i in range(len(errors)):
                    delaysums[i] += delays[i]
                muldimdelaysum += max(delays)

            for i in range(len(errors)):
                print(delaysums[i]/nbtuples,end=',')
            print(muldimdelaysum/nbtuples)
            
        return

    if args.reconstruct:
        for filename in files:
            for i in range(len(errors)):
                if errors[i] != -1:
                    data = streamfilelogicaltime(filename,i,args.sep)
                    timestream = logicaltimes(streamfile(filename,0,args.sep))
                    for (p,R) in compressors[i].genplastream(data, errors[i], timestream):
                        if R is not None:
                            L, m = R
                            if args.endpoints and len(L) > 1:
                                segment = list(L)
                                L = [segment[0],segment[-1]]
                            for (x,y) in L:
                                print(x,y,sep=args.sep)
        return

    times = 0
    if args.logicaltimes:
        times = 1
    elif args.realtimes:
        times = 2

    stats = plastatsdir(files, compressors, errors, times,
                        args.verbose, args.perfile, args.sep)

    if args.compression:
        print(stats['m']/stats['n'])
    if args.avgerror:
        print(stats['e']/stats['n'])
    if args.rmserror:
        print(sqrt(stats['s']/stats['n']))
    if args.maxerror:
        print(stats['x'])
    if args.delay:
        print(stats['d']/stats['n'])
    if args.discarded:
        print(stats['i'])
    if args.verbose:
        print("-"*80)
    if not (args.compression or args.avgerror or args.rmserror or args.maxerror
            or args.delay or args.discarded):
        print("Nb of files\t", len(files))
        printstatsall(stats,errors)
        
