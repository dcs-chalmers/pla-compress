
csvfilename1 = "cricket.csv"
csvfilename2 = "cricket_reconstructed.csv"

errors = []

with open(csvfilename1, 'r') as file_to_check:
    with open(csvfilename2, 'r') as file:
        for x in file_to_check.readlines():
            errors.append(abs(float(x)-float(file.readline())))

print("nb values \t", len(errors))
print("max error \t", round(max(errors),5))
print("average error \t", round(sum(errors)/len(errors),10))


            
