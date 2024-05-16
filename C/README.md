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

If the input is stored in a *single-column* (default) or *single-row* CSV/TSV format, the small util `csv2bin` can be used to stream the input to the PLA compressor, eg:

```
cat single_column_file.csv | ./csv2bin | ./linear-pla error_bound > ouput_pla.pla
```

```
cat csv_row_file.csv | ./csv2bin ',' | ./linear-pla error_bound > ouput_pla.pla
```

```
cat tsv_row_file.tsv | ./csv2bin '\t' | ./linear-pla error_bound > ouput_pla.pla
```

The following pipeline should have no problem to handle about **1M datapoints per second** on any recent laptop with the data stored on a local SSD.

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

## Demo static usage (small input file)

Here is a simple tutorial to test the software using an open dataset as example.

1. Compile the programs following the above instructions.
2. Retrieve the folders *CricketX*, *CricketY* and *CricketZ* from [UCR's website](https://www.cs.ucr.edu/%7Eeamonn/time_series_data_2018/).
3. Generate the sample time series input by running the following commands (*no dependencies*):<br />
```
cd example_data/; python3 gen_test_data.py; cd ..
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

Following the above pipeline for different error bounds make you appreciate the trade-off **accuracy** (eg *Mean Average Error*) versus **compression ratio** (ie *X times smaller size*):

| Error bound | Size of the PLA (in bytes)    | Compression Ratio (versus CSV input)* | Compression Ratio (versus float binary input)* | Average Error    |
| :---: | :---:  | :---: | :---: | :---:  |
| 0.115 | 1188208| 6.74  | 2.36  | 0.0408 |
| 0.41  | 400226 | 20.01 | 7.01  | 0.1235 |
| 0.602 | 280701 | 28.53 | 10.00 | 0.1648 |
| 1     | 173684 | 46.11 | 16.16 | 0.2422 |
| 1.15  | 249562 | 52.97 | 18.57 | 0.2721 |
| 1.238 | 140275 | 57.09 | 20.02 | 0.2883 |

(**NB*:** *The compresssion ratio depends if the input is the original 8009050-bytes CSV/TSV file or a single precision floating binary dump of 2808000 bytes. If the input data was originally stored using double precision, the compression ratio is roughly the double of the one obtained with binary float values. Note that the logical timestamps used by the compression technique do not need to be stored.*)

The number of segment/singletons can also be easily accessed:

```
cat example_data/cricket.bin | ./linear-pla 1 | ./pla-decompress 4 | wc -l
```

## Demo streaming usage

To illustrate the streaming usage, we can use the basic script `csv2socket.py` in `example_data`. The script simulates that the data is produced by eg a sensor at a rate of 200 values per second and the output is produced **as soon as ready**.

1. Run the generator program (which assumes the input csvfile is available, by default *cricket.csv*):<br />
```
cd example_data; python3 csv2socket.py; cd .. &
```
2. Read data from the generator socket and outputs segment informations only via `pla-decompress`:<br />
```
nc 127.0.0.1 12345 | ./linear-pla 1 | ./pla-decompress 4
```

## Demo large datafile

Let us also demonstrate here the performance of the compression technique on a larger data input in the example_dataset folder:

```
cd example_data/
```

1. To build a larger dataset from Geolife data, follow steps ("First steps") from the following guide: https://github.com/dcs-chalmers/dataloc_vn
2. Download and extract the [Geolife raw dataset](https://www.microsoft.com/en-us/download/details.aspx?id=52367&from=https%3A%2F%2Fresearch.microsoft.com%2Fen-us%2Fdownloads%2Fb16d359d-d164-469e-9fd4-daa38f2b2e13%2F).
3. Download the following script [genbeijing.py](https://github.com/dcs-chalmers/dataloc_vn/blob/master/scripts/datasets/genbeijing.py).
4. Update the `outdir` in the penultimate line of the script to indicate an already created target directory for the dataset, eg `mkdir -p beijing; sed -i -e 's/..\/..\/datasets\///g' genbeijing.py`.
5. Run the script with geolife directory as argument, eg `python3 genbeijing.py "Geolife Trajectories 1.3"`.
6. Wait for completetion, the above preprocessing may take a few minutes on a modern laptop.
7. Concatenate all data into a single 726-MB CSV file, eg: `cat ./beijing/* > beijing.csv`. 
8. Split the 4 channels (timestamp, longitude, latitude, altitude) of the file: <br>
```
cut -d, -f1 beijing.csv > beijing_ts.csv; cut -d, -f2 beijing.csv > beijing_x.csv; cut -d, -f3 beijing.csv > beijing_y.csv; cut -d, -f4 beijing.csv > beijing_z.csv
```
9. Test the PLA-compression on each file, eg: <br>
```cat example_data/beijing_ts.csv | ./csv2bin | ./linear-pla 0.01 > beijing_ts.pla```

Below are examples of compression ratios and execution time on a 2017 ultrabook (i7-7500U, 16GB RAM):

| Dataset | Number of datapoints    | Size CSV input (bytes) | Datarange | Error (<0.0025% of datarange) | Size PLA (bytes) | Compression Ratio (versus CSV input) | Average Error    | Execution time compression (s) | Execution time decompression (s) | Datapoint / second (compression) |
| :---: | :---:  | :---: | :---: | :---:  | :---: | :---:  | :---: | :---: | :---:  | :---:  |
| beijing_ts.csv | 21,140,001 | 125889029 | 86399.0 | 0.001  | 16575688 | 7.6 | 0.0000 | 18.1 | 15.5 | 1.2 M/s |
| beijing_x.csv | 21,140,001 | 223197238 | 10.00 | 0.0001  | 846724 | 23.4 | 3.00e-05 | 7.04 | 13.3 | 3 M/s |
| beijing_y.csv | 21,140,001 | 243488933 | 24.97 | 0.0002  | 6797096 | 35.82 |  5.65e-05 | 9.1 | 14.5 | 2.3 M/s |
| beijing_z.csv | 21,140,001 | 169039384 | 42712 | 1  | 16151565 | 10.5  | 0.2916  |  10.8 | 16 | 2 M/s |

(**NB**: *0.0001 maximum error in longitude/latitude is about ~10m. *)
