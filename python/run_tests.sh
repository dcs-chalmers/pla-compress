echo "running simple tests on example file ../testdata/jagged_testdata.txt"
echo "timestamps are logical, data spans a 1.45 range, i.e. 0.18 = 12.5% max error"
echo "----------------------------------------------------------------------------"
echo "Angular compressor only on second channel"
echo "python3 angle.py ../testdata/jagged_testdata.txt -1 0.18"
python3 angle.py ../testdata/jagged_testdata.txt -1 0.18
echo "----------------------------------------------------------------------------"
echo "Convex-Hull compressor only on second channel"
echo "python3 convexhull.py ../testdata/jagged_testdata.txt -1 0.18"
python3 convexhull.py ../testdata/jagged_testdata.txt -l -1 0.18
echo "----------------------------------------------------------------------------"
echo "Linear compressor only on second channel"
echo "python3 linear.py ../testdata/jagged_testdata.txt -1 0.18"
python3 linear.py ../testdata/jagged_testdata.txt -l -1 0.18
