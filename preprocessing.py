import math

import numpy as np
import torch
from gaussian_splatting.scene import Scene
import os
from tqdm import tqdm
from os import makedirs
from gaussian_splatting.gaussian_renderer import render
import torchvision
from gaussian_splatting.utils.general_utils import safe_state
from argparse import ArgumentParser
from gaussian_splatting.arguments import ModelParams, PipelineParams, get_combined_args
from gaussian_splatting.gaussian_renderer import GaussianModel
from gaussian_splatting.scene.cameras import Camera
from ab_utils import *
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.decomposition import PCA
import numpy as np
from scipy.spatial import KDTree

import time

all_elements = []
all_elements_by_name = {}  # dict with all the elements, every element has a list with all its ranges
element_count = {}
color_settings = {}
atom_coords = []
atom_color_list = []
all_elems_sorted_by_mn = []
unknown_label = 'n/a'
cov3D_list = []
volume_opacity_list = []

def get_indices():
    atom_index_list = []
    index = 0

    for elem_name in all_elements_by_name:
        num_displayed = all_elements_by_name[elem_name]['num_displayed']
        atom_index_list.extend([[index]] * num_displayed)
        index += 1

    return atom_index_list

def atom_color_update():
    global atom_color_list

    # reset color list
    atom_color_list = []

    for elem_name in all_elements_by_name:
        num_displayed = all_elements_by_name[elem_name]['num_displayed']

        col_struct = color_settings[elem_name]['color']
        col = (col_struct[0] / 255, col_struct[1] / 255, col_struct[2] / 255, col_struct[3])
        atom_color_list.append([col] * num_displayed)

    # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
    if len(atom_color_list) > 0 and isinstance(atom_color_list[0], list):
        atom_color_list = [x for xs in atom_color_list for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

    return atom_color_list


def atom_coords_update():
    # reset coords list
    global atom_coords
    global all_elements_by_name
    atom_coords = []
    # build coord list for shader
    for elem_name in all_elements_by_name:
        this_elem_coords = all_elements_by_name[elem_name]['coordinates']
        atom_coords.extend(this_elem_coords)

    # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
    if len(atom_coords) > 0 and isinstance(atom_coords[0], list):
        atom_coords = [x for xs in atom_coords for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

    return atom_coords


def combine_rrng_and_e_pos_file():
    all_atoms = all_elems_sorted_by_mn  # all atoms sorted by m/n

    # atoms and elements are sorted by m/n, so we can loop through the list from the start element (the first by defalt)
    # and increase the start index if the atom gets bigger than the current start element
    start_index = 0
    else_counter = 0

    # reset num_of_atoms values
    for elem in all_elements_by_name:
        all_elements_by_name[elem]['num_of_atoms'] = 0
        all_elements_by_name[elem]['coordinates'] = []

    for atom in all_atoms:
        added = 0
        m_n = atom[3]  # m/n of current atom
        this_elem = all_elements[start_index]

        # check if charge of this atom is between start and end range of the current element
        # if so, we have found the element of our atom
        if m_n >= this_elem['start_range'] and m_n <= this_elem['end_range']:
            # print('range of this element', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
            elem_name = this_elem['element_name']  # + '_' + str(this_elem['charge'])
            all_elements_by_name[elem_name]['coordinates'].append((atom[0], atom[1], atom[2]))
            added += 1

        # check if charge of this atom is smaller than start range of current element
        # if so, the element is unknown
        elif m_n < this_elem['start_range']:
            # print('smaller than smallest element -> unknown', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
            all_elements_by_name[unknown_label]['coordinates'].append((atom[0], atom[1], atom[2]))
            added += 1

        # check if charge of this atom is greater than end of current element
        # if so, we increase the start_index when searching in our element list
        elif m_n > this_elem['end_range']:
            # print('greater than this element -> increase start index', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
            if start_index + 1 < len(all_elements):
                start_index += 1
                # print('increase start index', m_n, this_elem['start_range'], this_elem['end_range'], start_index)

            # loop through the next atoms to check if the charge of this atom
            # matches the range of one of the next elements
            for i in range(start_index, len(all_elements)):
                this_elem = all_elements[i]

                # check if the charge of this atom matches the range of the current element in the loop
                # if so, we have found the element of the current atom
                if m_n >= this_elem['start_range'] and m_n <= this_elem['end_range']:
                    # print('range of next element', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
                    elem_name = this_elem['element_name']  # + '_' + str(this_elem['charge'])
                    all_elements_by_name[elem_name]['coordinates'].append((atom[0], atom[1], atom[2]))
                    added += 1
                    break

                # check if the charge of this atom is smaller than the start range of the current element in the loop
                # if so, we can't match this atom to an element in our list, so the element is unknown
                if m_n < this_elem['start_range']:
                    # print('unknown', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
                    all_elements_by_name[unknown_label]['coordinates'].append(
                        (atom[0], atom[1], atom[2]))
                    added += 1
                    break

                # check if the charge of this atom is greater than the end range of the current element
                # if so, we increase the start_index when searching in our element list
                if m_n > this_elem['end_range']:
                    else_counter += 1
                    all_elements_by_name[unknown_label]['coordinates'].append(
                        (atom[0], atom[1], atom[2]))
                    added += 1
                    # print('m_n greater than end range -> increasing start index if not last element', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
                    if start_index != len(all_elements) - 1:
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

    for elem in all_elements_by_name:
        num_of_atoms_sum += len(all_elements_by_name[elem]['coordinates'])

    if len(all_atoms) != num_of_atoms_sum:
        raise Exception('#atoms != #num_of_atoms_sum', len(all_atoms), num_of_atoms_sum)

    # build coord list for shader
    for elem in all_elements_by_name:
        # shuffle every element
        all_elements_by_name[elem]['coordinates'] = np.random.permutation(
            all_elements_by_name[elem]['coordinates'])
        all_elements_by_name[elem]['coordinates'] = [tuple(i) for i in
                                                     all_elements_by_name[elem]['coordinates']]
        this_elem_coords = all_elements_by_name[elem]['coordinates']
        all_elements_by_name[elem]['num_of_atoms'] = len(this_elem_coords)
        all_elements_by_name[elem]['num_displayed'] = len(this_elem_coords)

        all_elements_by_name[elem]['coordinates'] = np.asarray(all_elements_by_name[elem]['coordinates'])

    # disable the unknown atoms by default
    x = color_settings[unknown_label]
    color_settings[unknown_label]['display'] = False

    global atom_coords
    if isinstance(atom_coords[0], list):
        atom_coords = [x for xs in atom_coords for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

    return

def load_rrng_file():
    global color_settings
    global all_elements
    global all_elements_by_name

    # file_path = '/home/qa43nawu/temp/qa43nawu/input_files/voldata/rangefile.rrng'
    file_path = '/home/qa43nawu/temp/qa43nawu/input_files/CuAl50_Ni_2p3V_10min_02/CuAl50_Ni_range_file_030817.rrng'

    rrng_file = open(file_path, 'r')

    for line in rrng_file:
        if line.startswith('Range'):
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
            all_elements.append(this_element)

            # set the current general point size to all the element point sizes
            general_point_size = 5.0

            # add this element to element property group to create a color picker in the color settings tab
            elem_name = this_element['element_name']
            if elem_name not in color_settings:
                element_color_settings = {
                    "name": elem_name,
                    "display_name": elem_name,
                    "point_size": general_point_size,
                    "color": this_element['color'],
                    "display": True,
                }
                color_settings[element_color_settings['name']] = element_color_settings
                element_count[elem_name] = 0

            # add unknown label to the color settings dict
            element_color_settings = {
                "name": unknown_label,
                "display_name": unknown_label,
                "point_size": general_point_size,
                "color": [255, 0, 0, 1],
                "display": True,
            }
            color_settings[unknown_label] = element_color_settings

    # sort atoms by start range
    all_elements.sort(key=lambda x: x.get('start_range'))

    # build all_elements_by_name dict
    for elem in all_elements:
        name_and_charge = elem['element_name']

        if name_and_charge not in all_elements_by_name:
            this_element_dict = {}
            this_element_dict['element_name'] = elem['element_name']
            this_element_dict['color'] = elem['color']
            this_element_dict['coordinates'] = []
            this_element_dict['num_of_atoms'] = 0
            this_element_dict['num_displayed'] = 0
            all_elements_by_name[name_and_charge] = this_element_dict

    # if both (r)rng and (e)pos file are loaded, we combine these two files
    combine_rrng_and_e_pos_file()


def load_e_pos_file():
    file_path = '/home/qa43nawu/temp/qa43nawu/input_files/voldata/voldata.epos'
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

    # save the min and max x, y, z positions for camera settings later on
    # ABGlobals.max_x = concat_data[:, 0].max()
    # ABGlobals.min_x = concat_data[:, 0].min()
    # ABGlobals.max_y = concat_data[:, 1].max()
    # ABGlobals.min_y = concat_data[:, 1].min()
    # ABGlobals.max_z = concat_data[:, 2].max()
    # ABGlobals.min_z = concat_data[:, 2].min()

    # shuffling the data as they're kind of sorted by the z value
    concat_data = np.random.permutation(concat_data)

    num_of_atoms = int(num_of_atoms)
    concat_data = concat_data[:num_of_atoms]

    # sort atoms by ['m/n']
    global all_elems_sorted_by_mn
    sorted_by_mn = concat_data[concat_data[:, 3].argsort()]

    all_elems_sorted_by_mn = sorted_by_mn # todo ?? global

    coords = [(atom[0], atom[1], atom[2]) for atom in sorted_by_mn]

    # add unknown element to the list
    global atom_coords
    unknown_element_dict = {}
    unknown_element_dict['element_name'] = 'Unknown'
    unknown_element_dict['color'] = (255, 0, 0, 1)
    unknown_element_dict['coordinates'] = []
    unknown_element_dict['num_of_atoms'] = len(atom_coords)
    unknown_element_dict['num_displayed'] = len(atom_coords)
    all_elements_by_name[unknown_label] = unknown_element_dict

    atom_coords = coords
    all_elements_by_name[unknown_label]['coordinates'] = atom_coords
    all_elements_by_name[unknown_label]['num_of_atoms'] = len(atom_coords)

    return coords

def load_pos_file():
    file_path = '/home/qa43nawu/temp/qa43nawu/input_files/CuAl50_Ni_2p3V_10min_02/recons/recon-v02/default/R56_01519-v01.pos'
    # file_path = '/home/qa43nawu/Downloads/R14_27263-v01.pos'

    data_in_bytes = np.fromfile(file_path, dtype='>f')
    data_as_float = data_in_bytes.view()

    # calculating how many atoms we have as input; dividing by 11 because there are 11 features to store
    num_of_atoms = int(data_as_float.shape[0] / 4)
    reshaped_data = np.reshape(data_as_float, (num_of_atoms, 4))

    # save the min and max x, y, z positions for camera settings later on
    # ABGlobals.max_x = reshaped_data[:, 0].max()
    # ABGlobals.min_x = reshaped_data[:, 0].min()
    # ABGlobals.max_y = reshaped_data[:, 1].max()
    # ABGlobals.min_y = reshaped_data[:, 1].min()
    # ABGlobals.max_z = reshaped_data[:, 2].max()
    # ABGlobals.min_z = reshaped_data[:, 2].min()

    # shuffling the data as they're kind of sorted by the z value
    np.random.seed(0)
    reshaped_data = np.random.permutation(reshaped_data)

    debug_nom = 500

    reshaped_data = reshaped_data[:debug_nom]
    num_of_atoms = debug_nom

    # sort atoms by ['m/n']
    global all_elems_sorted_by_mn
    sorted_by_mn = reshaped_data[reshaped_data[:, 3].argsort()]

    all_elems_sorted_by_mn = sorted_by_mn # todo ?? global

    coords = [(atom[0], atom[1], atom[2]) for atom in sorted_by_mn]


    # add unknown element to the list
    unknown_element_dict = {}
    unknown_element_dict['element_name'] = 'Unknown'
    unknown_element_dict['color'] = (255, 0, 0, 1)
    unknown_element_dict['coordinates'] = []
    unknown_element_dict['num_of_atoms'] = num_of_atoms
    unknown_element_dict['num_displayed'] = num_of_atoms
    all_elements_by_name[unknown_label] = unknown_element_dict

    global atom_coords
    atom_coords = coords
    all_elements_by_name[unknown_label]['coordinates'] = atom_coords
    all_elements_by_name[unknown_label]['num_of_atoms'] = len(atom_coords)

    return coords

def calc_standard_deviation(distances, indices):

    # mean_x, mean_y, mean_z = np.mean(point_cloud, axis=0)
    # std_x, std_y, std_z = np.std(point_cloud, axis=0)
    #
    # num_sd = 3
    #
    # sd_range_lower = [mean_x - std_x * num_sd, mean_y - std_y * num_sd, mean_z - std_z * num_sd]
    # sd_range_upper = [mean_x + std_x * num_sd, mean_y + std_y * num_sd, mean_z + std_z * num_sd]
    #
    # within_std = point_cloud[
    #     (point_cloud[:, 0] >= sd_range_lower[0]) & (point_cloud[:, 0] <= sd_range_upper[0]) &
    #     (point_cloud[:, 1] >= sd_range_lower[1]) & (point_cloud[:, 1] <= sd_range_upper[1]) &
    #     (point_cloud[:, 2] >= sd_range_lower[2]) & (point_cloud[:, 2] <= sd_range_upper[2])
    # ]

    mean = np.mean(distances, axis=0)
    std = np.std(distances, axis=0)

    num_sd = 1

    sd_range_lower = mean - std * num_sd
    sd_range_upper = mean + std * num_sd

    within_std = indices[
        (distances[:] >= sd_range_lower) & (distances[:] <= sd_range_upper)
    ]

    return within_std

def calc_pca(point_cloud):
    # center data
    mean = np.mean(point_cloud, axis=0)
    centered_point_cloud = point_cloud - mean

    # covariance matrix of centered data (do we need this?)
    # cov_matrix = np.cov(centered_point_cloud, rowvar=False)

    # perform pca
    if len(centered_point_cloud.shape) == 1:
        centered_point_cloud = [centered_point_cloud]

    # num_components = 3 if len(centered_point_cloud) >= 3 else len(centered_point_cloud) # TODO for len < 3
    num_components = min(len(centered_point_cloud), 3)

    if num_components < 3:
        return np.asarray([[0.1, 0, 0], [0, 0.1, 0], [0, 0, 0.1]]), np.array([1,1,1])

    pca = PCA(n_components=num_components)

    pca.fit(centered_point_cloud)

    components = pca.components_
    explained_variance = pca.explained_variance_
    singular_values = pca.singular_values_

    volume_vec = explained_variance

    # transformed_cov_matrix = np.dot(components.T * explained_variance, components)
    # transformed_cov_matrix = np.dot(components.T * explained_variance * explained_variance, components)
    # transformed_cov_matrix = np.dot(components.T * singular_values, components)
    transformed_cov_matrix = np.dot(components.T * singular_values * singular_values, components)

    # if transformed_cov_matrix.ndim == 0 or transformed_cov_matrix.shape[0] != 3 or transformed_cov_matrix.shape[1] != 3: # TODO for len < 3
    #     mat_3x3 = np.zeros((3,3))
    #     mat_3x3[:2, :2] = transformed_cov_matrix
    #     transformed_cov_matrix = mat_3x3

    return transformed_cov_matrix, volume_vec

def find_nearest_neighbors(num_neighbors, max_distance, normalization):
    global cov3D_list, volume_opacity_list

    for elem in all_elements_by_name:
        coords = all_elements_by_name[elem][('coordinates')]
        if (len(coords) == 0):
            continue

        kdtree = KDTree(coords)

        for c in coords:
            query_coord = np.array(c)

            # get n nearest neighbors; only consider neighbors with distance < distance_upper_bound
            n = num_neighbors if all_elements_by_name[elem]['num_of_atoms'] >= num_neighbors else all_elements_by_name[elem]['num_of_atoms']
            distance, indices = kdtree.query(query_coord, k=n, distance_upper_bound=max_distance)

            filter = indices < len(coords)
            indices = indices[filter]
            distance = distance[filter]

            indices = calc_standard_deviation(distance, indices)

            indices = [indices]
            nn_coords = coords[indices][0]

            cov_mat, volume_vec = calc_pca(nn_coords)

            if np.isnan(np.asarray(cov_mat)).any():
                print(cov_mat)

            # if np.isnan(cov_mat).any(): # TODO fix nan
            #     # print(cov_mat)
            #     cov_mat = np.asarray([[0.1, 0, 0], [0, 0.1, 0], [0, 0, 0.1]])

            # print(cov_mat, "\n")


            eigenvalues, _ = np.linalg.eig(cov_mat)
            # volume = 4/3 * 3.14159 * eigenvalues[0] * eigenvalues[1] * eigenvalues[2]
            volume = 4/3 * 3.14159 * volume_vec[0] * volume_vec[1] * volume_vec[2]

            volume = volume / 50

            opacity = 1 / (0.25*volume)

            # opacity = 1 - opacity

            # print(opacity, "\n")

            cov_mat = cov_mat / normalization
            # print(eigenvalues, "\n")
            # print(volume, opacity, "\n")

            cov_mat = cov_mat.flatten()

            if np.isnan(cov_mat).any(): # TODO fix nan
                print(cov_mat)

            # if cov_mat[1] != cov_mat[3]:
            #     print('COVMAT13')
            #
            # if cov_mat[2] != cov_mat[6]:
            #     print('COVMAT26')
            #
            # if cov_mat[5] != cov_mat[7]:
            #     print('COVMAT57')

            reduced_covmat = np.zeros(6)
            reduced_covmat[0] = cov_mat[0]
            reduced_covmat[1] = cov_mat[1]
            reduced_covmat[2] = cov_mat[2]
            reduced_covmat[3] = cov_mat[4]
            reduced_covmat[4] = cov_mat[5]
            reduced_covmat[5] = cov_mat[8]

            cov_mat = reduced_covmat

            cov3D_list.append(np.asarray(cov_mat))
            volume_opacity_list.append([opacity])


if __name__ == "__main__":
    from argparse import Namespace

    args = Namespace(compute_cov3D_python=False, convert_SHs_python=True, data_device='cuda', debug=False, eval=False,
                     images='images', iteration=-1, model_path='/home/qa43nawu/temp/qa43nawu/gaussian_splatting/output/9224d987-c/', quiet=False, resolution=-1, sh_degree=3,
                     skip_test=False, skip_train=False, source_path='/home/qa43nawu/temp/qa43nawu/input_files/voldata',
                     white_background=False)

    ply_model = '/home/qa43nawu/temp/qa43nawu/gaussian_splatting/output/9224d987-c/'
    model = ModelParams(ply_model)
    dataset = model.extract(args)
    gaussians = GaussianModel(dataset.sh_degree)

    colmap_id = 1
    a_x = 1.57
    a_y = 3.14
    a_z = 0.0
    R_x = np.asarray([[1.0, 0.0, 0.0], [0.0, math.cos(a_x), -math.sin(a_x)], [0.0, math.sin(a_x), math.cos(a_x)]])
    R_y = np.asarray([[math.cos(a_y), 0.0, math.sin(a_y)], [0.0, 1.0, 0.0], [-math.sin(a_y), 0.0, math.cos(a_y)]])
    R_z = np.asarray([[math.cos(a_z), -math.sin(a_z), 0.0], [math.sin(a_z), math.cos(a_z), 0.0], [0.0, 0.0, 1.0]])
    R = np.matmul(np.matmul(R_x, R_y), R_z)
    T = np.asarray([0.0, -40.0, 200.0])

    props = {
        "colmap_id": colmap_id,
        "R": R,
        "T": T,
        "FoVx": 0.14,
        "FoVy": 0.28,
        "uid": 0,
        "scale": -2.0,
        "opacity": 1.0,
        "background_color": np.asarray([1.0, 1.0, 1.0]),
    }

    start = time.time()
    atom_coords = load_pos_file()

    print('load epos', time.time() - start)
    load_rrng_file()
    print('load rrng', time.time() - start)
    combine_rrng_and_e_pos_file()
    print('combine epos and rrng', time.time() - start)
    print('set colors', time.time() - start)

    indices = get_indices()

    path = '/home/qa43nawu/temp/qa43nawu/gaussian_splatting/output/9224d987-c/point_cloud/iteration_30000/point_cloud.ply'

    atom_color_list = atom_color_update()
    atom_coords_list = atom_coords_update()
    colors = np.asarray(atom_color_list)[:, :3]

    num_neighbors = 50
    max_distance = 20
    normalization = 500

    find_nearest_neighbors(num_neighbors, max_distance, normalization)
    # gaussians.cov3D = np.asarray(cov3D_list)

    gaussians.load_ply_ab(path, np.asarray(atom_coords), np.asarray(atom_color_list), np.asarray(cov3D_list), np.asarray(volume_opacity_list), np.asarray(indices), props)

    # write numbers of atom elements as comment
    comments = []
    for elem_name in all_elements_by_name:
        num_displayed = all_elements_by_name[elem_name]['num_displayed']
        color = str(all_elements_by_name[elem_name]['color']).split('(')[1].split(')')[0]
        color = color.split(',')
        comments.append(elem_name + "//" + str(num_displayed) + ' ' + str(color[0] + str(color[1]) + str(color[2])))

    comments.append('num_neighbors: ' + str(num_neighbors))
    comments.append('max_distance: ' + str(max_distance))
    comments.append('normalization: ' + str(normalization))

    # file_name = '/home/qa43nawu/temp/qa43nawu/out/point_cloud_neighb_' + str(num_neighbors) + '_dist_' + str(max_distance) + '.ply'
    file_name = '/home/qa43nawu/temp/qa43nawu/out/point_cloud_50' + '.ply'
    # file_name = '/home/qa43nawu/temp/qa43nawu/out/DEBUG_spiral.ply'
    gaussians.save_ply(file_name, colors, comments)