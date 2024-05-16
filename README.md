# Streaming PLA Compressor

This repository contains implementations of the PLA-based streaming compressor techniques that are presented in:

- \[1\] Havers, B., Duvignau, R., Najdataei, H., Gulisano, V., Papatriantafilou, M., & Koppisetty, A. C. (2020). DRIVEN: A framework for efficient Data Retrieval and clustering in Vehicular Networks. Future Generation Computer Systems, 107, 1-17.
- \[2\] Havers, B., Duvignau, R., Najdataei, H., Gulisano, V., Koppisetty, A. C., & Papatriantafilou, M. (2019, April). Driven: a framework for efficient data retrieval and clustering in vehicular networks. In 2019 IEEE 35th International Conference on Data Engineering (ICDE) (pp. 1850-1861). IEEE.
- \[3\] Duvignau, R., Gulisano, V., Papatriantafilou, M., & Savic, V. (2019, April). Streaming piecewise linear approximation for efficient data management in edge computing. In Proceedings of the 34th ACM/SIGAPP symposium on applied computing (pp. 593-596).
- \[4\] Duvignau, R., Gulisano, V., Papatriantafilou, M., & Savic, V. (2018). Piecewise linear approximation in data streaming: Algorithmic implementations and experimental analysis. arXiv preprint arXiv:1808.08877.

## Available implementations

We make two implementations available:

- [C Fast Implementation](C/): this is a fast implementation of our original *Linear PLA method* (a simple best-fit line calculation accelarated by maintaing convex-hulls) combined with the *Single Stream Protocol* to output segments and singletons in a *streaming fashion*. The program runs completely in a streaming fashion and can without modification or add-ons read data received from eg a network socket. The method and output protocol are the ones used in [1,2] and have been shown to offer the best trade-offs compression ratio / accuracy / latency as shown in [3,4]. Expected processing rate is above 1M datapoints per second. All parameters are fixed and the code provides only a simple basic interface. Only logical timestamps are suported.
- [Python Implementation](python/): this is a complete implementation of all methods (Angular, Linear and Convex-Hull) and streaming protocols presented in [3,4]. The code is meant to be flexible and versatile but not CPU-efficient. The program(s) offer a comprehensive interface to explore many variations of the methods' parameters, streaming output protocols, etc. The program can work with either a timestamp channel or logical timestamps and computes average delay to reconstruct multidimmensional input tuples.
