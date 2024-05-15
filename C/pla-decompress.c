/* Streaming PLA Single Stream Decompressor (C-implementation) by Romaric Duvignau, 2024, MIT License.
 * 
 * ---------------------------------------------------------------------------------------------------------
 * Please cite the following publications when used:
 * ---------------------------------------------------------------------------------------------------------
 * Duvignau, R., Gulisano, V., Papatriantafilou, M. and Savic, V., 2019, April. 
 * Streaming piecewise linear approximation for efficient data management in edge computing. 
 * In Proceedings of the 34th ACM/SIGAPP symposium on applied computing (pp. 593-596).
 * ---
 * Havers, B., Duvignau, R., Najdataei, H., Gulisano, V., Papatriantafilou, M. and Koppisetty, A.C., 2020. 
 * DRIVEN: A framework for efficient Data Retrieval and clustering in Vehicular Networks. 
 * Future Generation Computer Systems, 107, pp.1-17.
 * ---
 * Duvignau, R., Gulisano, V., Papatriantafilou, M. and Savic, V., 2018. 
 * Piecewise linear approximation in data streaming: Algorithmic implementations and experimental analysis. 
 * arXiv preprint arXiv:1808.08877.
 * ---------------------------------------------------------------------------------------------------------
 */

/* To compile:          gcc -std=gnu99 pla-decompress.c -o pla-decompress */  

/* Example usage:       cat data.pla | ./pla-decompress > data.csv */

#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>

#define VTYPE               float 

/* Default decompress to csv output, uncomment the marked lines to decompress to binary */

int main(int argc, char** argv){
    unsigned char n;
    VTYPE a, b, value;
    int x = 1;
    bool print_segments = false;
    char mode = 0;
    
    if(argc > 1){
        mode = atoi(argv[1]);
        /* Modes: 
         * 0,2      print text output (default), 
         * 1,3      print binary ouput
         * 2,3,4    print segments
         */
    }
    
    freopen(NULL, "rb", stdin);             // takes input from standard input in binary format
    
    if(mode%2 == 1)
        freopen(NULL, "wb", stdout);        // binary output
    
    while(true){
        if(fread(&n, sizeof(n), 1, stdin) != 1 || fread(&a, sizeof(a), 1, stdin) != 1) break;
        
        if(n == 1){
            if(mode >= 2)
                printf("%d <%d,%f>\n", x, n, a);                // print singleton
            if(mode == 0 || mode == 2)
                printf("%f\n", a);
            if(mode == 1 || mode == 3)
                fwrite(&a, sizeof(a), 1, stdout);               // uncomment for binary output
            
            x++;
        } 
        else{
            if(fread(&b, sizeof(b), 1, stdin) != 1) break;
            if(mode >= 2)
                printf("%d <%d,%f,%f>\n", x, n, a, b);          // print segment
                
            for(int i=0; i<n; i++){
                value = a*x+b;
                if(mode == 0 || mode == 2)
                    printf("%f\n", value);
                if(mode == 1 || mode == 3)
                    fwrite(&value, sizeof(value), 1, stdout);   // uncomment for binary output
                x++;
            }
        }
        
        fflush(stdout);
    }
    
    return EXIT_SUCCESS;
}
