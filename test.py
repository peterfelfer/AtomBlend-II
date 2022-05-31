import numpy as np

file_path = 'R56_03446-v01.epos'

# reading the given binary file and store it into a numpy array
# reading data as byte representation in float and int (as the last two values are ints we need a integer representation as well)
data_in_bytes_float = np.fromfile(file_path, dtype='>f')
data_in_bytes_int = np.fromfile(file_path, dtype='>i')

# converting byte data to float and int
data_as_float = data_in_bytes_float.view()
data_as_int = data_in_bytes_int.view()

# calculating how many atoms we have as input; dividing by 11 because there are 11 features to store
num_of_atoms = int(data_as_float.shape[0] / 11)

# reshaping so one atom has one row in the numpy array
reshaped_data_float = np.reshape(data_as_float, (num_of_atoms, 11))
reshaped_data_int = np.reshape(data_as_int, (num_of_atoms, 11))

# concatenate the first nine columns of float data and the last second columns from int data
concat_data = np.concatenate((reshaped_data_float[:, :9], reshaped_data_int[:, 9:]), axis=1)

num_of_atoms_percentage = int(num_of_atoms * 0.00001)
concat_data = concat_data[:num_of_atoms_percentage]

x = concat_data[concat_data[:,3].argsort()]

print(concat_data[:,3])
print(x[:,3])
a = [
     [12, 18, 6, 3],
     [ 4,  3, 1, 2],
     [15,  8, 9, 6]
]
a.sort(key=lambda x: x[1])

print(a)