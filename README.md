# Streaming PLA Compressor

This is a simple python implementation of the PLA-based streaming compressor techniques that are presented in:

- \[1\] Havers, B., Duvignau, R., Najdataei, H., Gulisano, V., Papatriantafilou, M., & Koppisetty, A. C. (2020). DRIVEN: A framework for efficient Data Retrieval and clustering in Vehicular Networks. Future Generation Computer Systems, 107, 1-17.
- \[2\] Havers, B., Duvignau, R., Najdataei, H., Gulisano, V., Koppisetty, A. C., & Papatriantafilou, M. (2019, April). Driven: a framework for efficient data retrieval and clustering in vehicular networks. In 2019 IEEE 35th International Conference on Data Engineering (ICDE) (pp. 1850-1861). IEEE.
- \[3\] Duvignau, R., Gulisano, V., Papatriantafilou, M., & Savic, V. (2019, April). Streaming piecewise linear approximation for efficient data management in edge computing. In Proceedings of the 34th ACM/SIGAPP symposium on applied computing (pp. 593-596).
- \[4\] Duvignau, R., Gulisano, V., Papatriantafilou, M., & Savic, V. (2018). Piecewise linear approximation in data streaming: Algorithmic implementations and experimental analysis. arXiv preprint arXiv:1808.08877.

## Usage

The code contains 3 compressors:

- **Angle** `angle.py`: simple angular compressor (a variant of "SwingFilter")
- **Convex-Hull** `convexhull.py`: optimal disjoint compressor (a variant of "SlideFilter")
- **Linear** `linear.py`: maitains a bestfit line through datapoints and uses convexhulls for quickly testing if the line breaks the error

The three programs use the same user interface. Simply run `python3 convexhull.py -h` to display a simple help:

```
usage: convexhull.py [-h] [-c] [-e] [-Q] [-m] [-d] [-i] [-I | -II | -III] [-b BND] [-t INPUTSIZE] [-o OUTPUTSIZE] [-S]
                     [-l] [-a] [-x] [-n] [-r] [-D] [-s SEP] [-p] [-v] [-q]
                     target errors [errors ...]

Compute different PLA statistics using by default the single stream protocol.

positional arguments:
  target                either a single file or a directory to process
  errors                list of maximum tolerated errors for PLA compr. for each channel; negative value= turn off PLA on
                        that channel

optional arguments:
  -h, --help            show this help message and exit
  -c, --compression     output only average compression
  -e, --avgerror        output only average error
  -Q, --rmserror        output only rms error
  -m, --maxerror        output only max error
  -d, --delay           output only average delay
  -i, --discarded       output only average discarded tuples
  -I, --twostream       set 2 streams protocol
  -II, --singlestreamv  set single stream variant protocol
  -III, --lidarvariant  set single stream lidar variant protocol
  -b BND, --bnd BND     set segment length bound; default=256; this bound also determines the number of bytes used to
                        encode the counter parameter in pla records
  -t INPUTSIZE, --inputsize INPUTSIZE
                        set input size in bytes; default=8;
  -o OUTPUTSIZE, --outputsize OUTPUTSIZE
                        set output size in bytes (for alpha/beta); default=8;
  -S, --singleoff       turn off singleton values
  -l, --logicaltimes    uses logical timestamps for all fields (default use channel 0 as time channel)
  -a, --realtimes       uses real timestamps for all fields as input (default use approximated channel 0)
  -x, --zip             outputs pla compression records
  -n, --endpoints       outputs pla segments' endpoints + singletons
  -r, --reconstruct     outputs reconstructed values
  -D, --ndelays         outputs average max delays (multi-dim. delays)
  -s SEP, --sep SEP     set datafile column sep; default=','
  -p, --perfile         if target is a directory, print statistics for each processed file
  -v, --verbose         increase output verbosity
  -q, --quiet           turn off output
```

## Tests 

After downloading the source code, simply execute `run_tests.sh` for running a few tests. 

## Input Format

The input format is **csv files** (the separator can be specified with the `-s` flag). 

By default, the first column is used as timestamps and the compressor runs over each column where an error is specified, e.g. `python3 convexhull.py -1 0.1 0.2` will use the first column as timestamps but do not attempt to compress it (since the chosen error is negative), the second column will be compressed with a max error of `0.1` and the third column with a max error of `0.2`.

To use logical timestamps (such that every column, including the timestamps column itself, is compressed against a counter, making compression and decompression decoupled from the timestamps column; see \[1\]), use flag `-l`.

The programs can also run over directories and will perform the compression on each file in the specified directory.

## Some examples of flags

`-1` is set to skip compression on a particular channel (here the first one).

`-II` uses a variant of single stream that aims at reducing data inflation upon using an error close to zero.

`-t` allows to set the input size of data values (default is 8 bytes or *double* precision). This influences compression ratios.

`-o` allows to set the output size for segments' parameters (alpha/beta, meaning slope and y-intercept of the segment). This influences compression ratios.

**To output pla segment records, use the `-x` flag.** The output depends on the chosen outputting protocol.

`-n` is *not implemented*.

`-v` adds some file info when running over a directory.

`-q` is *not implemented*. Use `python3 [...] 2> /dev/null` instead.

## Depedencies

None, the code only uses the standard python library (Python3 required). 

-------------------------

*Disclaimer: This is a highly experimental research code that has evolved by iteration, has not been thoroughly inspected in its latest installments and might not be completely bug free.*
