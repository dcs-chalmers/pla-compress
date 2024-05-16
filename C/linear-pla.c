/* Linear Streaming PLA Single Stream Compressor (C-implementation) by Romaric Duvignau, 2024, MIT License.
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

/* To compile:          gcc -std=gnu99 linear-pla.c -o linear-pla */ 

/* Example usage:       cat data.bin | ./linear-pla 1 > data.pla */

/* Documentation:
 * Single Stream Protocol associated with Linear PLA compression.
 * Timestamps are always logical in this implementation.
 * Default parameters: max segment size = 256 (1 byte encoding), a-b values as floats (4 bytes).
 * Segments of length 1-2 are encoded as singleton(s).
 * The Convex-Hulls have a  max size of 256 points by default.
 */

#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <math.h>

#define N_MAX               256             // limit segment size
#define N_TYPE              unsigned char   // update type for segment length so that N_MAX can fit within
#define MAX_HULL            256             // limit convex hull sizes for fitting in cache memory (their sizes won't likely exceed ~32)
#define VTYPE               float           // type for time series values and (a,b) ouput coefficients
#define VTYPE2              double          // type for sum calculations on the values
#define SINGLETONS          1               // boolean to deactivate singleton output
#define DELTA               0.000001        // floating point error extra tolerence

/* convex hulls */

VTYPE2 upper_hull[MAX_HULL];
VTYPE2 lower_hull[MAX_HULL];

int uhull_x[MAX_HULL];
int lhull_x[MAX_HULL];

int uhp = 0;    // uper hull pointer
int lhp = 0;    // lower hull pointer

/* 2-D utils */

VTYPE2 coeff_a(VTYPE2 x0, VTYPE2 y0, VTYPE2 x1, VTYPE2 y1) {return (y1-y0)/(x1-x0);}
VTYPE2 coeff_b(VTYPE2 x0, VTYPE2 y0, VTYPE2 x1, VTYPE2 y1) {return (x1*y0-y1*x0)/(x1-x0);}

VTYPE2 intersect(VTYPE2 x, VTYPE2 x0, VTYPE2 y0, VTYPE2 x1, VTYPE2 y1){ 
    return ((y1-y0)*x+x1*y0-y1*x0)/(x1-x0);
}

/* linear compressor */

int main(int argc, char** argv){
    VTYPE value, y, y0, y1, a, b, newa, newb, error;    // single precision
    VTYPE2 sumx, sumy, sumx2, sumxy;                    // double precision
    int x, x0, x1;                                      // logical timestamps
    N_TYPE n;                                           // segment size
    char singleton = 1;                                 // singleton n-value
    bool segment_KO;                                      
    int max_hull = 1;
    x = 0;
    x0 = -1;
    x1 = -1;
    
    if(argc < 2){
        printf("usage: cat binary_file.bin | %s error_bound\n", argv[0]);
        return EXIT_FAILURE;
    }
    
    error = atof(argv[1]);

    freopen(NULL, "rb", stdin);         // takes input from standard input in binary format
    freopen(NULL, "wb", stdout);        // writes output to standard output in binary format
    
    /* Read the very first 2 values */
    while(x < 2 && fread(&value, sizeof(value), 1, stdin) == 1){        // stops upon EOF        
        x += 1;
        
        if(x == 1){
            x0 = x;     y0 = value;
        } 
        else {
            x1 = x;     y1 = value;
        }
    }
    
    /* Process the rest of the streams */
    while(value != NAN){
        
        /* Initialize a new PLA segment */
        sumx = x0+x1;
        sumy = y0+y1;
        sumx2 = x0*x0+x1*x1;
        sumxy = x0*y0+x1*y1;
        a = coeff_a(x0, y0, x1, y1);
        b = coeff_b(x0, y0, x1, y1);
        
        /* Initialize the convex hulls */
        upper_hull[0] = y0+error;
        uhull_x[0] = x0;
        upper_hull[1] = y1+error;
        uhull_x[1] = x1;
        lower_hull[0] = y0-error;
        lhull_x[0] = x0;
        lower_hull[1] = y1-error;
        lhull_x[1] = x1;
        uhp = 2;
        lhp = 2;
        
        x = 2;
        n = 2;
        y = NAN;
        
        /* Process datapoints */
        while(fread(&value, sizeof(value), 1, stdin) == 1 && value != NAN){   // stops upon EOF or an NAN
            x += 1;
            y = value;
            n += 1;
            
            if(x >= N_MAX)
                break;
            
            // Check if (x,y) is within the limit slopes: terminate line ?
            sumx += x;
            sumy += y;
            sumx2 += x*x;
            sumxy += x*y;
            
            newa = (n*sumxy-sumx*sumy) / (n*sumx2-sumx*sumx);
            newb = (sumy-newa*sumx) / n;

            if( (x*newa+newb < y-error-DELTA) || (x*newa+newb > y+error+DELTA) ) 
                break;
            
            // Linear checking of the convex hulls
            segment_KO = false;
            
            for(int i=0; i<uhp; i++)
                if(newa*uhull_x[i]+newb > upper_hull[i]+DELTA){
                    segment_KO = true;
                    break;
                }
            
            if(segment_KO) break;

            for(int i=0; i<lhp; i++){
                if(newa*lhull_x[i]+newb < lower_hull[i]-DELTA){
                    segment_KO = true;
                    break;
                }
            }
            
            if(segment_KO) break;

            // New point accepted, now update the convex hulls
            
            // upper convex hull
            while(uhp > 1 && 
                intersect(x,uhull_x[uhp-2],upper_hull[uhp-2],uhull_x[uhp-1],upper_hull[uhp-1]) > y+error)
                uhp -= 1;
            uhull_x[uhp] = x;
            upper_hull[uhp] = y+error;
            uhp++;
            
            // lower convex hull
            while(lhp > 1 && 
                intersect(x,lhull_x[lhp-2],lower_hull[lhp-2],lhull_x[lhp-1],lower_hull[lhp-1]) < y-error)
                lhp -= 1;
            lhull_x[lhp] = x;
            lower_hull[lhp] = y-error;
            lhp++;
            
            // Update current best fit line
            a = newa;
            b = newb;
            
            if(n == 0)
                printf("\n %d, %d, %f, %f \n",x,n,a,b);
        }
        
        // End of input stream (EOF or a NAN value was received) => flush current segment
        if(y == NAN)
            break; 
        
        // End of current segment
        n -= 1;
        x = 2;                      // reset logical timestamps
        
        if (n == 1)                 // 2 last datapoints reached stop here and clean up after
            break;
        
        if(SINGLETONS && n == 2){       // flush 1 isolated point
            fwrite(&singleton, sizeof(singleton), 1, stdout);
            fwrite(&y0, sizeof(y0), 1, stdout);

            x0 = 1;      y0 = y1;       
            x1 = 2;      y1 = y;
        }
        else {               // flush one segment
            fwrite(&n, sizeof(n), 1, stdout);
            fwrite(&a, sizeof(a), 1, stdout);
            fwrite(&b, sizeof(b), 1, stdout);
            
            x0 = 1;                     // reset logical timestamps     
            x1 = -1;
            y0 = y;

            if(fread(&value, sizeof(value), 1, stdin) == 1 && value != NAN){
                x1 = 2;     y1 = value;
            }
            else
                break;
        }
        
        fflush(stdout);                 // flush standard output
    }
    
    // End of input stream => flush current segment
    if(x0 != -1){
        if(x1 == -1){
            fwrite(&singleton, sizeof(singleton), 1, stdout);
            fwrite(&y0, sizeof(y0), 1, stdout);
        }
        else if (n == 1){               // 2 last datapoints
            fwrite(&singleton, sizeof(singleton), 1, stdout);
            fwrite(&y0, sizeof(y0), 1, stdout);
            fwrite(&singleton, sizeof(singleton), 1, stdout);
            fwrite(&y1, sizeof(y1), 1, stdout);
        }
        else{
            fwrite(&n, sizeof(n), 1, stdout);
            fwrite(&a, sizeof(a), 1, stdout);
            fwrite(&b, sizeof(b), 1, stdout);
        }
    }

    return EXIT_SUCCESS;
}
