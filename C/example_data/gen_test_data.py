import struct

# 1) download CricketX, CricketY and CricketZ from UCR's website
# [https://www.cs.ucr.edu/%7Eeamonn/time_series_data_2018/]

# 2) aggregate all data

data = []
for a in ['X','Y','Z']:
    for b in ['TEST', 'TRAIN']:
        with open(f"Cricket{a}/Cricket{a}_{b}.tsv", 'r') as file:
            for line in file:
                data.extend(float(x) for x in line.split('\t')[1:])   # discard classes

# 3) binarize the input (4-bytes float expected as input) 

with open("cricket.bin", 'wb') as file:
    for value in data:
        file.write(struct.pack("f", value))

# 4) bin to csv for convenience

with open("cricket.csv", 'w') as outputfile:
    with open("cricket.bin", 'rb') as file:
        while True:
            value = file.read(4)
            if len(value) < 4:
                break
            print(round(struct.unpack("f", value)[0],8), file=outputfile)
