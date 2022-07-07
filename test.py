import numpy as np
import time

file_path = 'T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01.epos'
'''
start = time.perf_counter()
print('epos function entering', start)

# reading the given binary file and store it into a numpy array
# reading data as byte representation in float and int (as the last two values are ints we need a integer representation as well)
data_in_bytes_float = np.fromfile(file_path, dtype='>f')
data_in_bytes_int = np.fromfile(file_path, dtype='>i')

print('from file done', time.perf_counter() - start)

# converting byte data to float and int
data_as_float = data_in_bytes_float.view()
data_as_int = data_in_bytes_int.view()

print('view() done', time.perf_counter() - start)

# calculating how many atoms we have as input; dividing by 11 because there are 11 features to store
num_of_atoms = int(data_as_float.shape[0] / 11)

# reshaping so one atom has one row in the numpy array
reshaped_data_float = np.reshape(data_as_float, (num_of_atoms, 11))
reshaped_data_int = np.reshape(data_as_int, (num_of_atoms, 11))

print('reshaping done', time.perf_counter() - start)

# concatenate the first nine columns of float data and the last second columns from int data
concat_data = np.concatenate((reshaped_data_float[:, :9], reshaped_data_int[:, 9:]), axis=1)

print('concat done', time.perf_counter() - start)

num_of_atoms_percentage = int(num_of_atoms * 0.00001)
concat_data = concat_data[:num_of_atoms_percentage]

############################

from pathlib import Path
from functools import partial
from io import DEFAULT_BUFFER_SIZE

def file_byte_iterator():
     path = Path(file_path)
     with path.open('rb') as file:
        reader = partial(file.read1, DEFAULT_BUFFER_SIZE)
        file_iterator = iter(reader, bytes())
        print('hello')
        for chunk in file_iterator:
            yield from chunk


print('before file byte iterator', time.perf_counter() - start)
l = file_byte_iterator()
ll = list(l)
print('after file byte iterator', time.perf_counter() - start)
print(l)
print(ll)'''

import os
import array


# data_in_bytes_float = np.fromfile(file_path, dtype='>f')
start = time.perf_counter()
print('start 0')
a = array.array('f')
a.fromfile(open(file_path, 'rb'), os.path.getsize(file_path) // a.itemsize)

print('a.fromfile', time.perf_counter() - start)

print('NEW', os.path.getsize(file_path) // a.itemsize, a.itemsize)

data_as_float = np.array(a).view()
print('data_as_float', time.perf_counter() - start)
num_of_atoms = int(data_as_float.shape[0] / 11)
print('num_of_atoms', time.perf_counter() - start)
reshaped_data_float = np.reshape(data_as_float, (num_of_atoms, 11))

print('reshaped_data_float', time.perf_counter() - start)
print('end')
