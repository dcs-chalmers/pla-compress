// Small utils to stream a csv file (standard input) to binary (standard output)
// Delimiter can be configured: \n (Default), \t, "," etc

/* To compile:          gcc -std=gnu99 csv2bin.c -o csv2bin */  

/* Example usage:       cat data.csv | ./csv2bin > data.bin */

#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>

#define VTYPE               float 

/* Default decompress to csv output, uncomment the marked lines to decompress to binary */

int main(int argc, char** argv){
    char sep = '\n';
    VTYPE value;
    
    if(argc > 1)
        sep = argv[1][0];
    
    char pattern[3];
    pattern[0] = '%';
    pattern[1] = 'f';   // long float type
    pattern[2] = sep;

    freopen(NULL, "wb", stdout);        // binary output
    
    while(fscanf(stdin, pattern, &value) == 1) 
        fwrite(&value, sizeof(value), 1, stdout);
    
    return EXIT_SUCCESS;
}
