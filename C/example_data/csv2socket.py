import socket
import struct
import time
    
host = "localhost"
port = 12345

csvfile = "cricket.csv"

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as mysocket:
    mysocket.bind((host, port))
    mysocket.listen(10)

    client, address = mysocket.accept()

    with client:
        with open(csvfile, 'r') as file:
            for y in file:
                client.send(struct.pack("f",float(y)))
                time.sleep(0.0001)                # 10k values per second

        # send NaN to close the PLA compressor program
        client.send(struct.pack("f",float('nan')))

