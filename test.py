file_path = r'T:\Heller\AtomBlendII\alloy600TT\alloy600TT-RNGfile.rng'
rrng_file = open(file_path, 'r')

rrng_file.readline() # first line should be number of elements and ranges; we don't need this

# read the elements and their colors
line = rrng_file.readline()

all_elems = {}

while not line.startswith('-'):
    splitted_line = line.split(' ')
    if len(splitted_line) == 1:
        line = rrng_file.readline()
        continue

    this_element = {}

    # setting element name, charge is added later
    elem_name = splitted_line[0]
    this_element['element_name'] = elem_name

    # set color
    this_element['color'] = [splitted_line[1], splitted_line[2], splitted_line[3]]
    all_elems[elem_name] = this_element # todo: ABGlobals.all_elements; try with all_elements_by_name

    line = rrng_file.readline()

# get the elements from the line starting with '-------------------'
splitted_line = line.split(' ')
all_elements_by_order = []
for elem in range(1, len(splitted_line)):
    all_elements_by_order.append(splitted_line[elem])

# remove new line element and double spaces from list
all_elements_by_order[:] = (value for value in all_elements_by_order if value != '')
all_elements_by_order[:] = (value for value in all_elements_by_order if value != '\n')

line = rrng_file.readline()

while line.startswith('.'):
    splitted_line = line.replace('\n', ' ').split(' ')
    # remove new line element and double spaces from list
    print(splitted_line)
    splitted_line[:] = (value for value in splitted_line if value != '')
    print(splitted_line)


    line = rrng_file.readline()