import struct
import numpy as np

def main():
    # Little-endian float binary
    file_path = "/harddisk1/home.local/qa43nawu/input_files/voldata/voldata.epos"

    # Read little-endian float binary file
    with open(file_path, 'rb') as f:
        little_endian_data = f.read()

    # Convert little-endian floats to big-endian floats
    big_endian_data = bytearray()
    for i in range(0, len(little_endian_data), 4):  # Assuming each float is 4 bytes
        little_endian_float = struct.unpack('<f', little_endian_data[i:i + 4])[0]
        big_endian_float = struct.pack('>f', little_endian_float)
        big_endian_data.extend(big_endian_float)

    # Write big-endian data to a new file
    with open("/harddisk1/home.local/qa43nawu/input_files/voldata/voldata_be.epos", 'wb') as f:
        f.write(big_endian_data)


if __name__ == '__main__':
    main()