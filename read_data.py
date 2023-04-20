# MODULE DESCRIPTION:
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This includes all global variables that need to be accessable from all files

# ------------------- EXTERNAL MODULES -------------------
import bpy
import os
from bpy.props import FloatProperty, PointerProperty
from bpy.app.handlers import persistent
import math
from bpy_extras.io_utils import ImportHelper
import numpy as np
from dataclasses import dataclass
import time
import os
from .globals import ABGlobals

# ------------- Atom Data -------------
# Class that contains all relevant information about atoms in range files
from .shader_management import ABManagement


@dataclass
class AtomData:
    num_of_ion: int = 0
    num_of_range: int = 0
    start_range: float = 0.0
    end_range: float = 0.0
    vol: float = 0.0
    element = None
    charge: int = 0
    color = None

# ------------ GLOBAL VARIABLES ---------------
# CLASS USED FOR THE IMPORTANT GLOBAL VARIABLES AND LISTS IN THIS ADDON
class AtomBlendAddon:
    def setup(self, context):
        # set material mode in layer screen
        space = bpy.data.screens["Layout"]
        for s in space.areas:
            if s.type == 'VIEW_3D':

                s.spaces[0].shading.type = 'RENDERED'
                s.spaces[0].clip_end = 5000

        # set material mode in geometry nodes screen
        space = bpy.data.screens["Geometry Nodes"]
        for s in space.areas:
            if s.type == 'VIEW_3D':
                s.spaces[0].shading.type = 'RENDERED'

        # set render mode to cycles & GPU rendering
        bpy.data.scenes["Scene"].render.engine = 'CYCLES'
        bpy.data.scenes["Scene"].cycles.device = 'GPU'

        # change resolution to upright image
        bpy.data.scenes["Scene"].render.resolution_x = 1080
        bpy.data.scenes["Scene"].render.resolution_y = 1920

        # set camera location
        bpy.context.scene.atom_blend_addon_settings.camera_location_x_frame = 240.0
        bpy.context.scene.atom_blend_addon_settings.camera_location_y_frame = 0.0
        bpy.context.scene.atom_blend_addon_settings.camera_location_z_frame = 43.0

        # add the unknown element to color structures
        element_color_settings = bpy.context.scene.color_settings.add()
        element_color_settings.name = ABGlobals.unknown_label
        element_color_settings.display_name = ABGlobals.unknown_label
        element_color_settings.color = (0.4, 0.4, 0.4, 1.0)
        # element_color_settings.color = (1.0, 0.0, 0.0, 1.0)

        # add unknown element to the list
        unknown_element_dict = {}
        unknown_element_dict['element_name'] = 'Unknown'
        #unknown_element_dict['charge'] = 'n/a'
        # unknown_element_dict['color'] = (0.4, 0.4, 0.4, 1.0)
        unknown_element_dict['color'] = (1.0, 0.0, 0.0, 1.0)
        unknown_element_dict['coordinates'] = []
        unknown_element_dict['num_of_atoms'] = len(ABGlobals.atom_coords)
        unknown_element_dict['num_displayed'] = len(ABGlobals.atom_coords)
        ABGlobals.all_elements_by_name[ABGlobals.unknown_label] = unknown_element_dict

    def combine_rrng_and_e_pos_file(self, context):
        start = time.perf_counter()

        all_atoms = ABGlobals.all_data  # all atoms sorted by m/n
        all_elements = ABGlobals.all_elements

        # atoms and elements are sorted by m/n, so we can loop through the list from the start element (the first by defalt)
        # and increase the start index if the atom gets bigger than the current start element
        start_index = 0
        else_counter = 0

        # reset num_of_atoms values
        for elem in ABGlobals.all_elements_by_name:
            ABGlobals.all_elements_by_name[elem]['num_of_atoms'] = 0
            ABGlobals.all_elements_by_name[elem]['coordinates'] = []

        for atom in all_atoms:
            added = 0
            m_n = atom[3]  # m/n of current atom
            this_elem = all_elements[start_index]

            # check if charge of this atom is between start and end range of the current element
            # if so, we have found the element of our atom
            if m_n >= this_elem['start_range'] and m_n <= this_elem['end_range']:
                # print('range of this element', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
                elem_name = this_elem['element_name'] #+ '_' + str(this_elem['charge'])
                ABGlobals.all_elements_by_name[elem_name]['coordinates'].append((atom[0], atom[1], atom[2]))
                added += 1

            # check if charge of this atom is smaller than start range of current element
            # if so, the element is unknown
            elif m_n < this_elem['start_range']:
                # print('smaller than smallest element -> unknown', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
                ABGlobals.all_elements_by_name[ABGlobals.unknown_label]['coordinates'].append((atom[0], atom[1], atom[2]))
                added += 1

            # check if charge of this atom is greater than end of current element
            # if so, we increase the start_index when searching in our element list
            elif m_n > this_elem['end_range']:
                # print('greater than this element -> increase start index', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
                if start_index + 1 < len(all_elements):
                    start_index += 1
                    #print('increase start index', m_n, this_elem['start_range'], this_elem['end_range'], start_index)

                # loop through the next atoms to check if the charge of this atom
                # matches the range of one of the next elements
                for i in range(start_index, len(all_elements)):
                    this_elem = all_elements[i]

                    # check if the charge of this atom matches the range of the current element in the loop
                    # if so, we have found the element of the current atom
                    if m_n >= this_elem['start_range'] and m_n <= this_elem['end_range']:
                        # print('range of next element', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
                        elem_name = this_elem['element_name'] #+ '_' + str(this_elem['charge'])
                        ABGlobals.all_elements_by_name[elem_name]['coordinates'].append((atom[0], atom[1], atom[2]))
                        added += 1
                        break

                    # check if the charge of this atom is smaller than the start range of the current element in the loop
                    # if so, we can't match this atom to an element in our list, so the element is unknown
                    if m_n < this_elem['start_range']:
                        # print('unknown', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
                        ABGlobals.all_elements_by_name[ABGlobals.unknown_label]['coordinates'].append((atom[0], atom[1], atom[2]))
                        added += 1
                        break

                    # check if the charge of this atom is greater than the end range of the current element
                    # if so, we increase the start_index when searching in our element list
                    if m_n > this_elem['end_range']:
                        else_counter += 1
                        ABGlobals.all_elements_by_name[ABGlobals.unknown_label]['coordinates'].append((atom[0], atom[1], atom[2]))
                        added += 1
                        # print('m_n greater than end range -> increasing start index if not last element', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
                        if start_index != len(all_elements)-1:
                            start_index += 1
                        break

            # check if we really increased the element_count only one time
            if added != 1:
                print(added)
                for i in range(0, len(all_elements)):
                    elem = all_elements[i]
                    print(i, elem['start_range'], elem['end_range'])
                raise Exception('added not 1')

        num_of_atoms_sum = 0

        for elem in ABGlobals.all_elements_by_name:
            num_of_atoms_sum += len(ABGlobals.all_elements_by_name[elem]['coordinates'])

        if len(all_atoms) != num_of_atoms_sum:
            raise Exception('#atoms != #num_of_atoms_sum', len(all_atoms), num_of_atoms_sum)

        # build coord list for shader
        for elem in ABGlobals.all_elements_by_name:
            # shuffle every element
            ABGlobals.all_elements_by_name[elem]['coordinates'] = np.random.permutation(ABGlobals.all_elements_by_name[elem]['coordinates'])
            ABGlobals.all_elements_by_name[elem]['coordinates'] = [tuple(i) for i in ABGlobals.all_elements_by_name[elem]['coordinates']]
            this_elem_coords = ABGlobals.all_elements_by_name[elem]['coordinates']
            ABGlobals.all_elements_by_name[elem]['num_of_atoms'] = len(this_elem_coords)
            ABGlobals.all_elements_by_name[elem]['num_displayed'] = len(this_elem_coords)
            # print('READ DATA', elem)
            bpy.context.scene.color_settings[elem].perc_displayed = bpy.context.scene.atom_blend_addon_settings.vertex_percentage

        # disable the unknown atoms by default
        bpy.context.scene.color_settings[ABGlobals.unknown_label].display = False

        '''
        # build atom color list
        ABGlobals.atom_color_list = []

        for elem_name in ABGlobals.all_elements_by_name:
            elem_amount = ABGlobals.all_elements_by_name[elem_name]['num_of_atoms']

            col_struct = bpy.context.scene.color_settings[elem_name].color
            col = (col_struct[0], col_struct[1], col_struct[2], col_struct[3])
            ABGlobals.atom_color_list.append([col] * elem_amount)
            print(elem_name)

        # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if isinstance(ABGlobals.atom_color_list[0], list):
            ABGlobals.atom_color_list = [x for xs in ABGlobals.atom_color_list for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists
        '''

        # # update point size list
        # DisplaySettings.atom_color_update(self, context)

        if isinstance(ABGlobals.atom_coords[0], list):
            ABGlobals.atom_coords = [x for xs in ABGlobals.atom_coords for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

        # f = open(r'\tmp/unknown_coords.txt', 'w')
        # coords = ABGlobals.all_elements_by_name[ABGlobals.unknown_label]['coordinates']
        # for i in range(len(coords)):
        #     f.write(str(coords[i][0]) + '\t')
        #     f.write(str(coords[i][1]) + '\t')
        #     f.write(str(coords[i][2]) + '\t')
        #     f.write('\n')
        # f.close()

    def load_rng_file(self, context):
        if ABGlobals.path_rrng == None:
            print('No file loaded')
            return

        # if rng file is loaded first, init the unknown element into color structures
        if not ABGlobals.FileLoaded_e_pos:
            AtomBlendAddon.setup(self, context)

        file_path = ABGlobals.path_rrng
        rrng_file = open(file_path, 'r')

        rrng_file.readline()  # first line should be number of elements and ranges; we don't need this

        # read the elements and their colors
        line = rrng_file.readline()

        all_elems_color = {}  # store the colors of the elements as they are stated in a different section than the ranges

        while not line.startswith('-'):
            splitted_line = line.split(' ')

            if len(splitted_line) == 1:
                line = rrng_file.readline()
                continue

            splitted_line = line.replace('\n', ' ')
            splitted_line = splitted_line.replace(',', '.').split(' ')

            this_element = {}

            # setting element name, charge is added later
            elem_name = splitted_line[0]
            this_element['element_name'] = elem_name

            # set color
            # r = int(float(splitted_line[1]) * 255)
            # g = int(float(splitted_line[2]) * 255)
            # b = int(float(splitted_line[3]) * 255)
            r = float(splitted_line[1])
            g = float(splitted_line[2])
            b = float(splitted_line[3])

            this_element['color'] = (r, g, b, 1)
            all_elems_color[elem_name] = this_element  # todo: ABGlobals.all_elements; try with all_elements_by_name

            line = rrng_file.readline()

        # get the elements from the line starting with '-------------------'
        splitted_line = line.replace('\n', ' ').split(' ')
        all_elements_by_order = []
        for elem in range(1, len(splitted_line)):
            all_elements_by_order.append(splitted_line[elem])

        # remove new line element and double spaces from list
        all_elements_by_order[:] = (value for value in all_elements_by_order if value != '')
        all_elements_by_order[:] = (value for value in all_elements_by_order if value != '\n')
        line = rrng_file.readline()

        # read single atoms
        while line.startswith('.'):
            this_elem = {}
            this_elem['element_name'] = ''
            splitted_line = line.replace('\n', ' ')
            splitted_line = splitted_line.replace(',', '.').split(' ')
            # remove new line element and double spaces from list
            splitted_line[:] = (value for value in splitted_line if value != '')
            only_bitmask = splitted_line[3:]
            combined_elems = 0

            for i in range(len(only_bitmask)):
                if int(only_bitmask[i]) != 0:
                    elem_name = all_elements_by_order[i]

                    if int(only_bitmask[i]) == 1:
                        this_elem['element_name'] += all_elems_color[elem_name]['element_name']  # todo maybe all_elems_by_order is better
                    else:
                        this_elem['element_name'] += all_elems_color[elem_name]['element_name'] + only_bitmask[i]
                    this_elem['color'] = all_elems_color[elem_name]['color']
                    this_elem['start_range'] = float(splitted_line[1])
                    this_elem['end_range'] = float(splitted_line[2])
                    combined_elems += 1

            # only add element to list if its one single element. polyatomic elements will be added later
            if int(combined_elems) == 1:
                ABGlobals.all_elements.append(this_elem)

                # set the current general point size to all the element point sizes
                general_point_size = context.scene.atom_blend_addon_settings.point_size

                # add single elements to color_settings
                elem_name = this_elem['element_name']
                if elem_name not in bpy.context.scene.color_settings:
                    element_color_settings = bpy.context.scene.color_settings.add()
                    element_color_settings.name = elem_name
                    element_color_settings.display_name = elem_name
                    element_color_settings.point_size = general_point_size
                    element_color_settings.color = this_elem['color']
                    # element_color_settings.point_size = 5.0
                    ABGlobals.element_count[elem_name] = 0

            line = rrng_file.readline()

        # read polyatomic extensions
        while not line.startswith('-'):
            line = rrng_file.readline()

        # read '--- polyatomic extension' line
        line = rrng_file.readline()

        while not line.startswith('-'):
            splitted_line = line.split(' ')

            if len(splitted_line) != 4:
                line = rrng_file.readline()
                continue

            splitted_line = line.replace('\n', ' ')
            splitted_line = splitted_line.replace(',', '.').split(' ')
            this_element = {}

            # setting element name, charge is added later
            elem_name = splitted_line[0]
            this_element['element_name'] = elem_name

            # set color
            r = int(float(splitted_line[1]) * 255)
            g = int(float(splitted_line[2]) * 255)
            b = int(float(splitted_line[3]) * 255)
            this_element['color'] = (r, g, b, 1)
            all_elems_color[elem_name] = this_element  # todo: ABGlobals.all_elements; try with all_elements_by_name

            line = rrng_file.readline()

        # read ------------------- [elems]' line
        all_elements_by_order = []
        splitted_line = line.replace('\n', ' ').split(' ')
        for elem in range(1, len(splitted_line)):
            all_elements_by_order.append(splitted_line[elem])

        # remove new line element and double spaces from list
        all_elements_by_order[:] = (value for value in all_elements_by_order if value != '')
        all_elements_by_order[:] = (value for value in all_elements_by_order if value != '\n')

        for elem in range(1, len(splitted_line)):
            all_elements_by_order.append(splitted_line[elem])

        # read next line
        line = rrng_file.readline()

        # read ranges of polyatomic elements
        while line.startswith('.'):
            this_elem = {}
            this_elem['element_name'] = ''
            splitted_line = line.replace('\n', ' ')
            splitted_line = splitted_line.replace(',', '.').split(' ')

            # remove new line element and double spaces from list
            splitted_line[:] = (value for value in splitted_line if value != '')
            splitted_line[:] = (value for value in splitted_line if value != '\n')

            only_bitmask = splitted_line[3:]
            for i in range(len(only_bitmask)):
                if int(only_bitmask[i]) != 0:
                    elem_name = all_elements_by_order[i]
                    this_elem['element_name'] += all_elems_color[elem_name]['element_name']
                    this_elem['color'] = all_elems_color[elem_name]['color']
                    this_elem['start_range'] = float(splitted_line[1])
                    this_elem['end_range'] = float(splitted_line[2])
            ABGlobals.all_elements.append(this_elem)

            line = rrng_file.readline()

            # set the current general point size to all the element point sizes
            general_point_size = context.scene.atom_blend_addon_settings.point_size

            # add this element to element property group to create a color picker in the color settings tab
            elem_name = this_elem['element_name']  # + '_' + str(this_element['charge'])

            # add polyatomic elements to color_settings
            if elem_name not in bpy.context.scene.color_settings:
                element_color_settings = bpy.context.scene.color_settings.add()
                element_color_settings.name = elem_name
                element_color_settings.display_name = elem_name
                element_color_settings.point_size = general_point_size
                element_color_settings.color = this_elem['color']
                # element_color_settings.point_size = 5.0
                ABGlobals.element_count[elem_name] = 0

        # sort atoms by start range
        ABGlobals.all_elements.sort(key=lambda x: x.get('start_range'))

        # build all_elements_by_name dict
        for elem in ABGlobals.all_elements:
            name_and_charge = elem['element_name'] #+ '_' + str(elem['charge'])
            if name_and_charge not in ABGlobals.all_elements_by_name:
                this_element_dict = {}
                this_element_dict['element_name'] = elem['element_name']
                #this_element_dict['charge'] = elem['charge']
                this_element_dict['color'] = elem['color']
                this_element_dict['coordinates'] = []
                this_element_dict['num_of_atoms'] = 0
                this_element_dict['num_displayed'] = 0
                ABGlobals.all_elements_by_name[name_and_charge] = this_element_dict

        # if both (r)rng and (e)pos file are loaded, we combine these two files
        if(ABGlobals.FileLoaded_e_pos):
            AtomBlendAddon.combine_rrng_and_e_pos_file(self, context)

    def load_rrng_file(self, context):
        if(ABGlobals.path_rrng == None):
            print('No file loaded')
            return

        # if rrng file is loaded first, init the unknown element into color structures
        if not ABGlobals.FileLoaded_e_pos:
            AtomBlendAddon.setup(self, context)

        file_path = ABGlobals.path_rrng
        rrng_file = open(file_path, 'r')

        for line in rrng_file:
            if line.startswith('Range'):
                # this_element = AtomData()
                this_element = {}

                # splitting line by space
                splitted_line = line.split(' ')

                # setting num of range, start and end value of range
                first_string = splitted_line[0].split('=')
                range_num = first_string[0].split('e')[1]
                this_element['num_of_range'] = float(range_num)

                start_range = first_string[1].replace(',', '.')
                this_element['start_range'] = float(start_range)
                end_range = splitted_line[1].replace(',', '.')
                this_element['end_range'] = float(end_range)

                # setting vol value of range
                vol = splitted_line[2].split(':')
                vol = vol[1].replace(',', '.')
                this_element['vol'] = float(vol)

                # setting element name and charge
                amount_index = 3
                this_element['element_name'] = ''
                while splitted_line[amount_index].split(':')[0] != 'Color':
                    elem = splitted_line[amount_index].split(':')
                    if elem[1] != '1':
                        this_element['element_name'] += elem[0] + elem[1]
                    else:
                        this_element['element_name'] += elem[0]
                    amount_index += 1
                    #this_element['amount'] = int(elem[1])

                # setting atomic number
                #this_element['atomic_number'] = ABGlobals.atomic_numbers[this_element['element_name']]

                # setting the color
                color_index = amount_index
                hex_col = splitted_line[color_index].split(':')
                hex_col = hex_col[1].replace('\n', '')

                # convert hex to rgb color
                r_hex = hex_col[0:2]
                g_hex = hex_col[2:4]
                b_hex = hex_col[4:6]
                rgb_color = (int(r_hex, 16), int(g_hex, 16), int(b_hex, 16), 1)

                this_element['color'] = rgb_color

                # add this element to element list
                ABGlobals.all_elements.append(this_element)

                # set the current general point size to all the element point sizes
                general_point_size = context.scene.atom_blend_addon_settings.point_size

                # add this element to element property group to create a color picker in the color settings tab
                elem_name = this_element['element_name'] #+ '_' + str(this_element['charge'])
                if elem_name not in bpy.context.scene.color_settings:
                    element_color_settings = bpy.context.scene.color_settings.add()
                    element_color_settings.name = elem_name
                    element_color_settings.display_name = elem_name
                    element_color_settings.point_size = general_point_size
                    element_color_settings.color = this_element['color']
                    # element_color_settings.point_size = 5.0
                    ABGlobals.element_count[elem_name] = 0

        # sort atoms by start range
        ABGlobals.all_elements.sort(key=lambda x: x.get('start_range'))

        # build all_elements_by_name dict
        for elem in ABGlobals.all_elements:
            name_and_charge = elem['element_name'] #+ '_' + str(elem['charge'])

            if name_and_charge not in ABGlobals.all_elements_by_name:
                this_element_dict = {}
                this_element_dict['element_name'] = elem['element_name']
                #this_element_dict['charge'] = elem['charge']
                this_element_dict['color'] = elem['color']
                this_element_dict['coordinates'] = []
                this_element_dict['num_of_atoms'] = 0
                this_element_dict['num_displayed'] = 0
                ABGlobals.all_elements_by_name[name_and_charge] = this_element_dict

        # if both (r)rng and (e)pos file are loaded, we combine these two files
        if(ABGlobals.FileLoaded_e_pos):
            AtomBlendAddon.combine_rrng_and_e_pos_file(self, context)

    def load_epos_file(self, context):
        if (ABGlobals.path == None):
            print('No file loaded')
            return

        if context.scene.atom_blend_addon_settings.dev_mode:
            bpy.ops.wm.console_toggle()

        # set dataset name
        filename = ABGlobals.path.split(sep='\\')[-1]
        ABGlobals.dataset_name = filename.split(sep='.')[0]

        # if epos file is loaded first, init the unknown element into color structures
        if not ABGlobals.FileLoaded_rrng:
            AtomBlendAddon.setup(self, context)

        file_path = ABGlobals.path

        start = time.perf_counter()

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

        # reducing the atom data by a certain percentage by only taking the first n elements
        atoms_percentage = context.scene.atom_blend_addon_settings.vertex_percentage

        # save the min and max x, y, z positions for camera settings later on
        # ABGlobals.min_z_value = float(concat_data[0, 2])
        # ABGlobals.max_z_value = float(concat_data[-1, 2])
        ABGlobals.max_x = concat_data[:, 0].max()
        ABGlobals.min_x = concat_data[:, 0].min()
        ABGlobals.max_y = concat_data[:, 1].max()
        ABGlobals.min_y = concat_data[:, 1].min()
        ABGlobals.max_z = concat_data[:, 2].max()
        ABGlobals.min_z = concat_data[:, 2].min()

        #print(ABGlobals.max_x, ABGlobals.min_x, ABGlobals.max_y, ABGlobals.min_y, ABGlobals.max_z, ABGlobals.min_z)
        # shuffling the data as they're kind of sorted by the z value
        concat_data = np.random.permutation(concat_data)

        num_of_atoms = int(num_of_atoms)
        concat_data = concat_data[:num_of_atoms]

        # sort atoms by ['m/n']
        sorted_by_mn = concat_data[concat_data[:, 3].argsort()]
        ABGlobals.all_data = sorted_by_mn

        coords = [(atom[0], atom[1], atom[2]) for atom in sorted_by_mn]

        ABGlobals.atom_coords = coords
        ABGlobals.all_elements_by_name[ABGlobals.unknown_label]['coordinates'] = ABGlobals.atom_coords
        ABGlobals.all_elements_by_name[ABGlobals.unknown_label]['num_of_atoms'] = len(ABGlobals.atom_coords)

        # if both rrng and (e)pos file are loaded, we combine these two files
        # AtomBlendAddon.e_pos_shader_prep(self, context)
        if(ABGlobals.FileLoaded_rrng):
            AtomBlendAddon.combine_rrng_and_e_pos_file(self, context)

        # activate camera preview
        context.space_data.region_3d.view_perspective = 'CAMERA'

        ABManagement.init(self, context)

    def load_pos_file(self, context):
        start = time.perf_counter()
        if (ABGlobals.path == None):
            print('No file loaded')
            return

        # set dataset name
        filename = ABGlobals.path.split(sep='\\')[-1]
        ABGlobals.dataset_name = filename.split(sep='.')[0]

        # if pos file is loaded first, init the unknown element into color structures
        if not ABGlobals.FileLoaded_rrng:
            AtomBlendAddon.setup(self, context)

        file_path = ABGlobals.path
        data_in_bytes = np.fromfile(file_path, dtype='>f')
        data_as_float = data_in_bytes.view()

        # calculating how many atoms we have as input; dividing by 11 because there are 11 features to store
        num_of_atoms = int(data_as_float.shape[0] / 4)
        reshaped_data = np.reshape(data_as_float, (num_of_atoms, 4))

        # reducing the atom data by a certain percentage by only taking the first n elements
        #atoms_percentage = context.scene.atom_blend_addon_settings.vertex_percentage / 100

        # save the min and max x, y, z positions for camera settings later on
        ABGlobals.max_x = reshaped_data[:, 0].max()
        ABGlobals.min_x = reshaped_data[:, 0].min()
        ABGlobals.max_y = reshaped_data[:, 1].max()
        ABGlobals.min_y = reshaped_data[:, 1].min()
        ABGlobals.max_z = reshaped_data[:, 2].max()
        ABGlobals.min_z = reshaped_data[:, 2].min()

        # shuffling the data as they're kind of sorted by the z value
        reshaped_data = np.random.permutation(reshaped_data)

        #num_of_atoms_percentage = int(num_of_atoms * atoms_percentage)
        #reshaped_data_percentage = reshaped_data[:num_of_atoms_percentage]

        # sort atoms by ['m/n']
        sorted_by_mn = reshaped_data[reshaped_data[:, 3].argsort()]

        ABGlobals.all_data = sorted_by_mn
        coords = [(atom[0], atom[1], atom[2]) for atom in sorted_by_mn]
        ABGlobals.atom_coords = coords
        ABGlobals.all_elements_by_name[ABGlobals.unknown_label]['coordinates'] = ABGlobals.atom_coords
        ABGlobals.all_elements_by_name[ABGlobals.unknown_label]['num_of_atoms'] = len(ABGlobals.atom_coords)

        # if both rrng and (e)pos file are loaded, we combine these two files
        if (ABGlobals.FileLoaded_rrng):
            AtomBlendAddon.combine_rrng_and_e_pos_file(self, context)

        # activate camera preview
        context.space_data.region_3d.view_perspective = 'CAMERA'

        ABManagement.init(self, context)
