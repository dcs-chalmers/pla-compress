# Single-Stream Linear PLA Compressor, fast implementation

This is a simple and fast **C implementation** of the PLA compression technique called *Linear* associated with the *Single-Stream Output Protocol* that are presented in:

- Havers, B., Duvignau, R., Najdataei, H., Gulisano, V., Papatriantafilou, M., & Koppisetty, A. C. (2020). DRIVEN: A framework for efficient Data Retrieval and clustering in Vehicular Networks. Future Generation Computer Systems, 107, 1-17.
- Havers, B., Duvignau, R., Najdataei, H., Gulisano, V., Koppisetty, A. C., & Papatriantafilou, M. (2019, April). Driven: a framework for efficient data retrieval and clustering in vehicular networks. In 2019 IEEE 35th International Conference on Data Engineering (ICDE) (pp. 1850-1861). IEEE.
- Duvignau, R., Gulisano, V., Papatriantafilou, M., & Savic, V. (2019, April). Streaming piecewise linear approximation for efficient data management in edge computing. In Proceedings of the 34th ACM/SIGAPP symposium on applied computing (pp. 593-596).
- Duvignau, R., Gulisano, V., Papatriantafilou, M., & Savic, V. (2018). Piecewise linear approximation in data streaming: Algorithmic implementations and experimental analysis. arXiv preprint arXiv:1808.08877.

## Usage

The program reads binary input from the standard input. By default the input's type are *single precision (4-bytes) floats*. 

Upon building a segment (or singleton), the program outputs directly to standard output in the format: **<1, y>** for a singleton with value **y** (default *float*) and **<n, a, b>** with **n** the segment length (default 1-byte *unsigned char*) and (**a**,**b**) the coefficients of the segment (encoded as *floats* by default).

### Example of static usage (non-streaming use-case)

If the full file is stored on disk, then one can use the following command to generate the PLA over the entire data (the program ends upon reaching the EOF):

```
cat binary_file.bin | ./linear-pla error_bound > ouput_pla.pla
```

### Example of usage receiving the input from the network

Since the program is conceived from the start to work in a streaming fashion, it can by default receives its input from eg a TCP socket, eg:

```
nc 127.0.0.1 12345 | ./linear-pla 1 | streaming_application_using_the_pla
```

To stop the program from running in that usage, you need to send a value equals to *NaN* (in the same type as the time series values).

### Example of usage for the decompression program

The decompression program defaults to ouput values in ASCII directly on standard output, eg:

```
cat ouput_pla.pla | ./pla-decompress [mode]
```

This can be change with the following modes:

- mode=0 (default)
- mode=1 outputs in binary format
- mode=2 outputs in text format and includes segments/singletons when produced
- mode=3 same as 2 but with binary output for the reconstructed values
- mode=4 only outputs segments/singletons in ASCII

## Compilation

You need to compile the C-code as follows:

```
gcc -std=gnu99 linear-pla.c -o linear-pla
```

To also be able to decompress the PLA, you will need to compile the decompressor program:

```
gcc -std=gnu99 pla-decompress.c -o pla-decompress
```

## Demo static usage

Here is a simple tutorial to test the software using an open dataset as example.

1. Compile the programs following the above instructions.
2. Retrieve the folders *CricketX*, *CricketY* and *CricketZ* from [UCR's website](https://www.cs.ucr.edu/%7Eeamonn/time_series_data_2018/).
3. Generate the sample time series input by running the following commands (*no dependencies*):<br />
```
cd example_data/
python3 gen_test_data.py
cd ..
```
4. Run the PLA compressor on the sample data using an error threshold of 1:<br />
```
cat example_data/cricket.bin | ./linear-pla 1 > example_data/cricket.pla
```
5. Run the PLA decompressor on the sample data:<br />
```
cat example_data/cricket.pla | ./pla-decompress > example_data/cricket_reconstructed.csv
```
6. Check that the reconstructed PLA satisfies the error threshold that was provided to construct the PLA:<br />
```
cd example_data
python3 check-pla.py
```
7. Compare the data sizes used on disk, eg:<br />
```
du -b example_data/*.bin example_data/*.pla
```

## Demo streaming usage

To illustrate the streaming usage, we can use the basic script `csv2socket.py` in `example_data`. The script simulates that the data is read by eg a sensor at a rate of 10k values per second. 

1. Run the generator program (which assumes the input csvfile is available, by default *cricket.csv*):<br />
```
cd example_data; python3 csv2socket.py; cd .. &
```
2. Read data from the generator socket and outputs segment informations only via `pla-decompress`:<br />
```
nc locahost 12345 | ./linear-pla 1 | ./pla-decompress 4
```
