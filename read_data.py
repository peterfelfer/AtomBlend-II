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


    # if both rrng and (e)pos file are loaded, this function is called
    def combine_rrng_and_e_pos_file(self):
        print('both files loaded!')

        point_cloud = bpy.data.objects['Atoms']
        point_cloud.data.attributes.new(name='element', type='INT', domain='POINT')
        point_cloud.data.attributes.new(name='charge', type='FLOAT', domain='POINT')

        m_n = AtomBlendAddon.all_data[:, 3:4]

        elements = []

        for mn in m_n:
            element_found = False
            for elem in AtomBlendAddon.all_elements:
                if elem['start_range'] <= mn <= elem['end_range']:
                    element_found = True
                    this_elem_name = elem['atomic_number']
                    elements.append(this_elem_name)

            if not element_found:
                elements.append(-1)

        point_cloud.data.attributes['element'].data.foreach_set('value', elements)
        print(bpy.data.materials)

        # add materials
        for elem in AtomBlendAddon.all_elements:
            name_and_charge = elem['element_name'] + '_' + str(elem['charge'])
            if bpy.data.materials.get(name_and_charge) is None:
                mat = bpy.data.materials.new(name=name_and_charge)
                mat.diffuse_color = elem['color']

                point_cloud.data.materials.append(mat)
        print(bpy.data.materials)

        # add node groups
        node_counter = 0
        base_node_group = bpy.data.node_groups['Geometry Nodes']

        # remove instance on points node as we use this node in each group
        node_to_remove = base_node_group.nodes['Instance on Points']
        base_node_group.nodes.remove(node_to_remove)

        # add input to base node group
        # base_node_group.nodes['Group Input'].tree_socket_add(in_out='IN')
        base_node_group.inputs.new('NodeSocketInt', 'element')

        bpy.ops.object.convert(target='POINTCLOUD')

        for mat in bpy.data.materials:
            print(mat.name)
            if mat.name == 'Dots Stroke' or mat.name == 'Material': # todo why?
                continue

            split_mat_name = mat.name.split('_')
            print(split_mat_name)
            atomic_number = AtomBlendAddon.atomic_numbers[split_mat_name[0]]

            node_group = bpy.data.node_groups.new(mat.name, 'GeometryNodeTree')
            group_inputs = node_group.nodes.new('NodeGroupInput')
            # group_inputs.location = (0, 0)
            # node_group.inputs.new('Geometry', name='Atoms')


            # node_group.inputs.new('Geometry', name='Geometry')

            # point_cloud.modifiers["GeometryNodes"]["Input_1_attribute_name"]

            compare_node = node_group.nodes.new('ShaderNodeMath')
            compare_node.operation = 'COMPARE'
            compare_node.inputs[1].default_value = atomic_number
            compare_node.inputs[2].default_value = 0.0
            compare_node.location = (200, -150)

            cube_node = node_group.nodes.new('GeometryNodeMeshCube')
            cube_node.inputs[0].default_value = (0.2, 0.2, 0.2)
            cube_node.location = (-30, -100)

            iop_node = node_group.nodes.new('GeometryNodeInstanceOnPoints')
            iop_node.location = (400, 0)

            set_material_node = node_group.nodes.new('GeometryNodeSetMaterial')
            set_material_node.inputs[2].default_value = mat
            set_material_node.location = (600, 0)

            group_outputs = node_group.nodes.new('NodeGroupOutput')
            group_outputs.location = (800, 0)
            node_group.outputs.new('Geometry', 'Output Geometry')

            # set input for node value
            # bpy.ops.object.geometry_nodes_input_attribute_toggle()
            # bpy.ops.object.geometry_nodes_input_attribute_toggle(prop_path="[\"Input_1_use_attribute\"]", modifier_name="GeometryNodes")

            # add geometry node of this element to the base node group
            element_group = base_node_group.nodes.new('GeometryNodeGroup')
            element_group.node_tree = bpy.data.node_groups[mat.name]
            element_group.location = (-25, node_counter * 150)
            # geometry_nodes_base_group.nodes.new('C_1')
            # bpy.ops.node.add_node(type='GeometryNodeGroup')

            # link nodes
            node_group.links.new(group_inputs.outputs[0], iop_node.inputs[0])
            node_group.links.new(group_inputs.outputs[1], compare_node.inputs[0])
            node_group.links.new(compare_node.outputs[0], iop_node.inputs[1])
            # node_group.links.new(cube_node.outputs[0], iop_node.inputs[2])
            node_group.links.new(iop_node.outputs[0], set_material_node.inputs[0])
            node_group.links.new(set_material_node.outputs[0], group_outputs.inputs[0])

            # link nodes in base geometry node group
            base_node_group.links.new(base_node_group.nodes['Group Input'].outputs[0], element_group.inputs[0])
            base_node_group.links.new(base_node_group.nodes['Group Input'].outputs[1], element_group.inputs[1])
            base_node_group.links.new(element_group.outputs[0], base_node_group.nodes['Join Geometry'].inputs[0])



            node_counter += 1

        # for gnmod in point_cloud.modifiers:
        #     # node_group.inputs.new('NodeSocketInt', name='Atomic number')
        #     print('gnmod', gnmod)
        #     # bpy.ops.object.geometry_nodes_input_attribute_toggle(prop_path="[\"Input_1_use_attribute\"]", modifier_name="GeometryNodes")
        #     # bpy.context.object.modifiers["GeometryNodes"].Input_1_use_attribute = "element"
        #
        #     # if gnmod.type == "NODES":
        #     #     break
        #     print('type', gnmod.type)
        #
        #     inputs = gnmod.node_group.inputs
        #     print('inputs', inputs)
        #     if "Value" not in inputs:
        #         print('if')
        #         inputs.new("NodeSocketInt", "Value")
        #
        #     id = inputs["Value"].identifier
        #     print('id', id)
        #     gnmod[id] = "element"
        #     gnmod[id] = True




        point_cloud.data.attributes['charge'].data.foreach_set('value', m_n.ravel())
        # point_cloud.data.attributes['material_index'].data.foreach_set('value', elem.ravel())

        # add geometry nodes
        geometry_nodes_group = bpy.data.node_groups['Geometry Nodes']




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
        geometry_nodes_group.links.new(mesh_node.outputs[0], iop_node.inputs[2])
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
                # this_atom = AtomData()
                this_atom = {}

                # splitting line by space
                splitted_line = line.split(' ')

                # setting num of range, start and end value of range
                first_string = splitted_line[0].split('=')
                range_num = first_string[0].split('e')[1]
                this_atom['num_of_range'] = float(range_num)

                start_range = first_string[1].replace(',', '.')
                this_atom['start_range'] = float(start_range)
                end_range = splitted_line[1].replace(',', '.')
                this_atom['end_range'] = float(end_range)

                # setting vol value of range
                vol = splitted_line[2].split(':')
                vol = vol[1].replace(',', '.')
                this_atom['vol'] = float(vol)

                # setting element name and charge
                elem = splitted_line[3].split(':')
                this_atom['element_name'] = elem[0]
                this_atom['charge'] = int(elem[1])

                # setting atomic number
                print(this_atom['element_name'], AtomBlendAddon.atomic_numbers)
                this_atom['atomic_number'] = AtomBlendAddon.atomic_numbers[this_atom['element_name']]

                # setting the color
                hex_col = splitted_line[4].split(':')
                hex_col = hex_col[1].replace('\n', '')

                # convert hex to rgb color
                r_hex = hex_col[0:2]
                g_hex = hex_col[2:4]
                b_hex = hex_col[4:6]
                rgb_color = (int(r_hex, 16), int(g_hex, 16), int(b_hex, 16), 1)

                this_atom['color'] = rgb_color
                # print(this_atom)

                # add this atom to atom list
                AtomBlendAddon.all_elements.append(this_atom)

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