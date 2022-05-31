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

# ------------- Atom Data -------------
# Class that contains all relevant information about atoms in range files
import AtomBlend


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
    # addon name
    name = None

    # path to the addon directory
    addon_path = bpy.path.abspath(os.path.dirname(os.path.realpath(__file__)))

    # The active Window and Viewport the user is currently working in
    BlenderWindow = None
    BlenderViewport = None

    # Rendering status
    RenderInvoked = False
    RenderAnimation = None

    # path: str = None
    FileLoaded_e_pos = False
    FileLoadedRRNG = False

    path: str = None
    path_rrng: str = None

    # atom data
    all_elements = []
    all_data = []
    atomic_numbers = []

    def setup(self, context):
        # set material mode in layer screen
        space = bpy.data.screens["Layout"]
        for s in space.areas:
            if s.type == 'VIEW_3D':
                s.spaces[0].shading.type = 'RENDERED'

        # set material mode in geometry nodes screen
        space = bpy.data.screens["Geometry Nodes"]
        for s in space.areas:
            if s.type == 'VIEW_3D':
                s.spaces[0].shading.type = 'RENDERED'

        # set render mode to cycles & GPU rendering
        bpy.data.scenes["Scene"].render.engine = 'CYCLES'
        bpy.data.scenes["Scene"].cycles.device = 'GPU'

    def combine_rrng_and_e_pos_file(self):
        print('both files loaded!')

        point_cloud = bpy.data.objects['Atoms']
        point_cloud.data.attributes.new(name='element', type='INT', domain='POINT')
        point_cloud.data.attributes.new(name='charge', type='FLOAT', domain='POINT')

        # get position
        num_atoms = len(point_cloud.data.attributes['m/n'].data)
        atom_positions = np.zeros(num_atoms * 3, dtype=np.float)
        num_of_atoms = int(len(atom_positions) / 3)
        point_cloud.data.vertices.foreach_get('co', atom_positions)
        atom_positions = np.reshape(atom_positions, (num_of_atoms, 3))

        # match every atom to element according to m_n
        pc_mn = point_cloud.data.attributes['m/n']

        # dict with one entry per element, atoms are stored in an array for each element
        elem_verts = {}
        elem_verts['unknown_element'] = []  # atoms that couldn't be matched to an element

        # loop through all the atoms and check all element if m/n fits the range of this element
        vert_count = 0
        for v in pc_mn.data:
            element_found = False
            for elem in AtomBlendAddon.all_elements:
                start_range = elem['start_range']
                end_range = elem['end_range']
                elem_name = elem['element_name'] + '_' + str(elem['charge'])

                print('elem_verts')
                for i in elem_verts:
                    print(i)

                if elem_name not in elem_verts:
                    print('if', elem_name)
                    elem_verts[elem_name] = []

                if v.value >= start_range and v.value <= end_range:
                    element_found = True
                    print('if', v.value, start_range, end_range, elem_name)
                    pos = atom_positions[vert_count]
                    elem_verts[elem_name].append((pos[0], pos[1], pos[2]))

            if not element_found:
                pos = atom_positions[vert_count]
                elem_verts['unknown_element'].append((pos[0], pos[1], pos[2]))

            vert_count += 1


        # create own object for each element and convert them to point clouds afterwards
        for elem_name in elem_verts:
            this_elem_mesh = bpy.data.meshes.new(elem_name)

            this_elem_mesh.from_pydata(elem_verts[elem_name], [], [])
            this_elem_mesh.update()

            this_elem_object = bpy.data.objects.new(elem_name, this_elem_mesh)
            bpy.context.collection.objects.link(this_elem_object)

            bpy.data.objects[elem_name].select_set(True)
            bpy.ops.object.convert(target='POINTCLOUD')

        # we can remove the atoms object as each element has its own object now
        bpy.data.objects.remove(bpy.data.objects['Atoms'], do_unlink=True)

        # todo: wrong context bug?
        # todo: make geometry node for each element -> color with element



    def make_mesh_from_vertices(self):
        ### visualize every vertex we have as mesh (currently: icosphere)
        # make new node group
        bpy.ops.node.new_geometry_nodes_modifier()
        geometry_nodes_group = bpy.data.node_groups['Geometry Nodes']


        # geometry_nodes_group.select_all()
        # geometry_nodes_group.group_make()

        # all_atoms_group = bpy.data.node_groups['AllAtoms']

        # add new nodes
        input_node = geometry_nodes_group.nodes['Group Input']
        output_node = geometry_nodes_group.nodes['Group Output']
        iop_node = geometry_nodes_group.nodes.new(type='GeometryNodeInstanceOnPoints')
        mesh_node = geometry_nodes_group.nodes.new(type='GeometryNodeMeshCube')
        # mesh_node.location = (-300, -100)
        # mesh_node.inputs[0].default_value = 0.3
        join_geometry_node = geometry_nodes_group.nodes.new(type='GeometryNodeJoinGeometry')
        join_geometry_node.location = (200, 100)
        output_node.location = (400, 100)


        # link nodes
        geometry_nodes_group.links.new(input_node.outputs[0], iop_node.inputs[0])
        # geometry_nodes_group.links.new(mesh_node.outputs[0], iop_node.inputs[2])
        geometry_nodes_group.links.new(iop_node.outputs[0], join_geometry_node.inputs[0])
        geometry_nodes_group.links.new(input_node.outputs[0], join_geometry_node.inputs[0])
        geometry_nodes_group.links.new(join_geometry_node.outputs[0], output_node.inputs[0])



    def load_rrng_file(self, context):
        print('LOADING .RRNG FILE')
        if(AtomBlendAddon.path_rrng == None):
            print('No file loaded')
            return

        file_path = AtomBlendAddon.path_rrng
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
                elem = splitted_line[3].split(':')
                this_element['element_name'] = elem[0]
                this_element['charge'] = int(elem[1])

                # setting atomic number
                print(this_element['element_name'], AtomBlendAddon.atomic_numbers)
                this_element['atomic_number'] = AtomBlendAddon.atomic_numbers[this_element['element_name']]

                # setting the color
                hex_col = splitted_line[4].split(':')
                hex_col = hex_col[1].replace('\n', '')

                # convert hex to rgb color
                r_hex = hex_col[0:2]
                g_hex = hex_col[2:4]
                b_hex = hex_col[4:6]
                rgb_color = (int(r_hex, 16), int(g_hex, 16), int(b_hex, 16), 1)

                this_element['color'] = rgb_color
                # print(this_element)

                # add this atom to atom list
                AtomBlendAddon.all_elements.append(this_element)

        # sort atoms by start range
        AtomBlendAddon.all_elements.sort(key=lambda x: x.get('start_range'))

        # if both rrng and (e)pos file are loaded, we combine these two files
        if(AtomBlendAddon.FileLoaded_e_pos):
            AtomBlendAddon.combine_rrng_and_e_pos_file(self)


    def load_epos_file(self, context):
        print('LOADING .EPOS FILE')
        if (AtomBlendAddon.path == None):
            print('No file loaded')
            return

        start = time.perf_counter()
        print('start', start)

        AtomBlendAddon.setup(self, context)

        # file_path = 'T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01.epos'
        file_path = AtomBlendAddon.path

        # reading the given binary file and store it into a numpy array
        # reading data as byte representation in float and int (as the last two values are ints we need a integer representation as well)
        data_in_bytes_float = np.fromfile(file_path, dtype='>f')
        data_in_bytes_int = np.fromfile(file_path, dtype='>i')

        print('reading bin', time.perf_counter() - start)

        # converting byte data to float and int
        data_as_float = data_in_bytes_float.view()
        data_as_int = data_in_bytes_int.view()

        print('converting', time.perf_counter() - start)

        # calculating how many atoms we have as input; dividing by 11 because there are 11 features to store
        num_of_atoms = int(data_as_float.shape[0] / 11)
        print('calc atoms', time.perf_counter() - start)

        # reshaping so one atom has one row in the numpy array
        reshaped_data_float = np.reshape(data_as_float, (num_of_atoms, 11))
        reshaped_data_int = np.reshape(data_as_int, (num_of_atoms, 11))
        print('reshaping', time.perf_counter() - start)

        # concatenate the first nine columns of float data and the last second columns from int data
        concat_data = np.concatenate((reshaped_data_float[:, :9], reshaped_data_int[:, 9:]), axis=1)
        print('concat', time.perf_counter() - start)

        # creating the mesh in blender
        # create a new mesh and a new object
        mesh = bpy.data.meshes.new("point-cloud")  # add a new mesh
        point_cloud = bpy.data.objects.new("Atoms", mesh)  # add a new object using the mesh

        print('creating mesh in blender', time.perf_counter() - start)

        # reducing the atom data by a certain percentage by only taking the first n elements
        atoms_percentage = context.scene.atom_blend_addon_settings.vertex_percentage / 100

        # shuffling the data as they're kind of sorted by the z value
        # TODO: is shuffling the data a problem?
        print('before shuffle', time.perf_counter() - start)

        # percentage_data = []
        # counter = 0
        # print(concat_data)
        # print(concat_data[0])
        # for i in concat_data:
        #     # print(i)
        #     if counter == 0:
        #         percentage_data.append(i)
        #         counter += 1
        #     elif counter == 100:
        #         counter = 0
        #     else:
        #         counter += 1



        concat_data = np.random.permutation(concat_data)
        concat_data_percentage = concat_data
        print('shuffle', time.perf_counter() - start)

        num_of_atoms_percentage = int(num_of_atoms * atoms_percentage)
        concat_data_percentage = concat_data[:num_of_atoms_percentage]
        AtomBlendAddon.all_data = concat_data_percentage

        print('concat', time.perf_counter() - start)

        # iterate over atoms and add them to coords list
        # for atom in concat_data_percentage:
        #     x = atom[0]
        #     y = atom[1]
        #     z = atom[2]
        #     coords.append((x, y, z))

        coords = [(atom[0], atom[1], atom[2]) for atom in concat_data_percentage]
        print('adding verts', time.perf_counter() - start)

        # Make a mesh from a list of vertices/edges/faces
        mesh.from_pydata(coords, [], [])

        # update the mesh
        mesh.update()

        # Link object to the active collection
        bpy.context.collection.objects.link(point_cloud)

        # select generated object
        point_cloud.select_set(True)
        bpy.context.view_layer.objects.active = point_cloud

        ### attributes of point_cloud
        # generate attributes on currently selected object point_cloud
        point_cloud.data.attributes.new(name='m/n', type='FLOAT', domain='POINT')
        point_cloud.data.attributes.new(name='TOF', type='FLOAT', domain='POINT')
        point_cloud.data.attributes.new(name='Vspec', type='FLOAT', domain='POINT')
        point_cloud.data.attributes.new(name='Vap', type='FLOAT', domain='POINT')
        point_cloud.data.attributes.new(name='xdet', type='FLOAT', domain='POINT')
        point_cloud.data.attributes.new(name='ydet', type='FLOAT', domain='POINT')
        point_cloud.data.attributes.new(name='delta pulse', type='FLOAT', domain='POINT')
        point_cloud.data.attributes.new(name='ions/pulse', type='FLOAT', domain='POINT')

        print('new attributes', time.perf_counter() - start)

        # extract columns of data
        m_n = concat_data_percentage[:, 3:4]
        tof = concat_data_percentage[:, 4:5]
        vspec = concat_data_percentage[:, 5:6]
        vap = concat_data_percentage[:, 6:7]
        xdet = concat_data_percentage[:, 7:8]
        ydet = concat_data_percentage[:, 8:9]
        delta_pulse = concat_data_percentage[:, 9:10]
        ions_pulse = concat_data_percentage[:, 10:11]

        print('SHAPE ', m_n.shape)

        # set attribute values in point_cloud
        point_cloud.data.attributes['m/n'].data.foreach_set('value', m_n.ravel())
        print('foreach mn', time.perf_counter() - start)
        point_cloud.data.attributes['TOF'].data.foreach_set('value', tof.ravel())
        print('tof', time.perf_counter() - start)
        point_cloud.data.attributes['Vspec'].data.foreach_set('value', vspec.ravel())
        print('vspec', time.perf_counter() - start)
        point_cloud.data.attributes['Vap'].data.foreach_set('value', vap.ravel())
        print('vap', time.perf_counter() - start)
        point_cloud.data.attributes['xdet'].data.foreach_set('value', xdet.ravel())
        print('xdet', time.perf_counter() - start)
        point_cloud.data.attributes['ydet'].data.foreach_set('value', ydet.ravel())
        print('ydet', time.perf_counter() - start)
        point_cloud.data.attributes['delta pulse'].data.foreach_set('value', delta_pulse.ravel())
        print('delta pulse', time.perf_counter() - start)
        point_cloud.data.attributes['ions/pulse'].data.foreach_set('value', ions_pulse.ravel())
        print('ions pulse', time.perf_counter() - start)

        print('attributes', time.perf_counter() - start)

        AtomBlendAddon.make_mesh_from_vertices(self)

        print('combine', time.perf_counter() - start)

        # if both rrng and (e)pos file are loaded, we combine these two files
        if(AtomBlendAddon.FileLoadedRRNG):
            AtomBlendAddon.combine_rrng_and_e_pos_file(self)

        print('end', time.perf_counter() - start)



    def load_pos_file(self, context):
        print('LOADING .POS FILE')
        if (AtomBlendAddon.path == None):
            print('No file loaded')
            return

        AtomBlendAddon.setup(self, context)


    # file_path = 'T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01.epos'
        file_path = AtomBlendAddon.path
        # data_in_bytes = np.fromfile(file_path, dtype='uint8')
        data_in_bytes = np.fromfile(file_path, dtype='>f')
        print(data_in_bytes)
        data_as_float = data_in_bytes.view()

        # calculating how many atoms we have as input; dividing by 11 because there are 11 features to store
        num_of_atoms = int(data_as_float.shape[0] / 4)
        reshaped_data = np.reshape(data_as_float, (num_of_atoms, 4))
        print('SHAPE: ', reshaped_data.shape)

        # create a new mesh and a new object
        mesh = bpy.data.meshes.new("point-cloud")  # add a new mesh
        point_cloud = bpy.data.objects.new("Atoms", mesh)  # add a new object using the mesh

        # reducing the atom data by a certain percentage by only taking the first n elements
        atoms_percentage = context.scene.atom_blend_addon_settings.vertex_percentage / 100

        # shuffling the data as they're kind of sorted by the z value
        # TODO: is shuffling the data a problem?
        reshaped_data = np.random.permutation(reshaped_data)

        num_of_atoms_percentage = int(num_of_atoms * atoms_percentage)
        # print(num_of_atoms, num_of_atoms_percentage)
        reshaped_data_percentage = reshaped_data[:num_of_atoms_percentage]
        AtomBlendAddon.all_data = reshaped_data_percentage

        coords = [(atom[0], atom[1], atom[2]) for atom in reshaped_data_percentage]

        # Make a mesh from a list of vertices/edges/faces
        mesh.from_pydata(coords, [], [])

        # update the mesh
        mesh.update()

        # Link object to the active collection
        bpy.context.collection.objects.link(point_cloud)

        # select generated object
        point_cloud.select_set(True)
        bpy.context.view_layer.objects.active = point_cloud

        ### attributes of point_cloud
        # generate attributes on currently selected object point_cloud
        point_cloud.data.attributes.new(name='m/n', type='FLOAT', domain='POINT')

        # extract columns of data
        m_n = reshaped_data_percentage[:, 3:4]

        # set attribute values in point_cloud
        point_cloud.data.attributes['m/n'].data.foreach_set('value', m_n.ravel())

        AtomBlendAddon.make_mesh_from_vertices(self)

        # if both rrng and (e)pos file are loaded, we combine these two files
        if (AtomBlendAddon.FileLoadedRRNG):
            AtomBlendAddon.combine_rrng_and_e_pos_file(self)