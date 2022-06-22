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
from AtomBlend.globals import ABGlobals

# ------------- Atom Data -------------
# Class that contains all relevant information about atoms in range files
import AtomBlend
from AtomBlend.shader_management import ABManagement


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
    # # addon name
    # name = None
    #
    # # path to the addon directory
    # addon_path = bpy.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    #
    # # The active Window and Viewport the user is currently working in
    # BlenderWindow = None
    # BlenderViewport = None
    #
    # # Rendering status
    # RenderInvoked = False
    # RenderAnimation = None
    #
    # # path: str = None
    # FileLoaded_e_pos = False
    # FileLoadedRRNG = False
    #
    # path: str = None
    # path_rrng: str = None
    #
    # # atom data
    # all_elements = []
    # all_data = []
    # atomic_numbers = []
    # element_count = {} # counts the amount of each element to pass the correct amount of colors to the shader later

    # prepare for shader after loading rrng file, i.e. reset stuff done in e_pos_shader_prep()
    def rrng_shader_prep(self, context):
        bpy.context.scene.color_settings.remove(0)

    # prepare for shader after loading (e)pos file when rrng file is not loaded
    def e_pos_shader_prep(self, context):
        element_color_settings = bpy.context.scene.color_settings.add()
        element_color_settings.name = 'Unknown_n/a'
        element_color_settings.color = (0.4, 0.4, 0.4, 1.0)

        # add unknown element to the list
        unknown_element_dict = {}
        unknown_element_dict['element_name'] = 'Unknown'
        unknown_element_dict['charge'] = 'n/a'
        unknown_element_dict['color'] = (0.4, 0.4, 0.4, 1.0)
        unknown_element_dict['coordinates'] = []
        unknown_element_dict['num_of_atoms'] = len(ABGlobals.atom_coords)
        ABGlobals.all_elements_by_name['Unknown_n/a'] = unknown_element_dict

        ABManagement.init_shader()

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

    def combine_rrng_and_e_pos_file_new_new(self, context):
        all_atoms = ABGlobals.all_data  # all atoms sorted by m/n

        for atom in all_atoms:
            m_n = atom[3]
            element_found = False

            for elem in ABGlobals.all_elements:
                if m_n >= elem['start_range'] and m_n <= elem['end_range']:
                    name_and_charge = elem['element_name'] + '_' + str(elem['charge'])

                    # # if the current element is not already in all_elements, add it
                    # if name_and_charge not in ABGlobals.all_elements:
                    #     ABGlobals.all_elements[name_and_charge] = {}

                    ABGlobals.all_elements_by_name[name_and_charge]['coordinates'].append((atom[0], atom[1], atom[2]))
                    element_found = True

            if not element_found:
                ABGlobals.all_elements_by_name['Unknown_n/a']['coordinates'].append((atom[0], atom[1], atom[2]))

        # build coord list for shader
        coords = []
        for elem in ABGlobals.all_elements_by_name:
            this_elem_coords = ABGlobals.all_elements_by_name[elem]['coordinates']
            ABGlobals.all_elements_by_name[elem]['num_of_atoms'] = len(this_elem_coords)
            coords.append(this_elem_coords)

        ABGlobals.atom_coords = coords
        print('combine rrng and epos', len(coords))
        for elem in ABGlobals.all_elements_by_name:
            # print(ABGlobals.all_elements_by_name[elem], 'LEN', len(ABGlobals.all_elements_by_name[elem]['coordinates']))
            print('LEN', ABGlobals.all_elements_by_name[elem]['element_name'], len(ABGlobals.all_elements_by_name[elem]['coordinates']))

        ABManagement.init_shader()

    def combine_rrng_and_e_pos_file_new(self, context):
        all_atoms = ABGlobals.all_data  # all atoms sorted by m/n
        all_elements = ABGlobals.all_elements

        print(all_atoms[:,3])
        print(all_elements)

        print(ABGlobals.element_count)

        # atoms and elements are sorted by m/n, so we can loop through the list from the start element (the first by defalt)
        # and increase the start index if the atom gets bigger than the current start element
        start_index = 0
        else_counter = 0

        start = time.perf_counter()
        print('start atom counting', start)

        for atom in all_atoms:
            added = 0
            m_n = atom[3]  # m/n of current atom
            this_elem = all_elements[start_index]

            # check if charge of this atom is between start and end range of the current element
            # if so, we have found the element of our atom
            if m_n >= this_elem['start_range'] and m_n <= this_elem['end_range']:
                # print('range of this element', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
                elem_name = this_elem['element_name'] + '_' + str(this_elem['charge'])
                ABGlobals.element_count[elem_name] += 1
                added += 1

            # check if charge of this atom is smaller than start range of current element
            # if so, the element is unknown
            elif m_n < this_elem['start_range']:
                # print('smaller than smallest element -> unknown', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
                ABGlobals.element_count['Unknown_n/a'] += 1
                added += 1

            # check if charge of this atom is greater than end of current element
            # if so, we increase the start_index when searching in our element list
            elif m_n > this_elem['end_range']:
                # print('greater than this element -> increase start index', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
                if start_index + 1 < len(all_elements):
                    start_index += 1

                # loop through the next atoms to check if the charge of this atom
                # matches the range of one of the next elements
                for i in range(start_index, len(all_elements)):
                    this_elem = all_elements[i]

                    # check if the charge of this atom matches the range of the current element in the loop
                    # if so, we have found the element of the current atom
                    if m_n >= this_elem['start_range'] and m_n <= this_elem['end_range']:
                        # print('range of next element', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
                        elem_name = this_elem['element_name'] + '_' + str(this_elem['charge'])
                        ABGlobals.element_count[elem_name] += 1
                        added += 1
                        break

                    # check if the charge of this atom is smaller than the start range of the current element in the loop
                    # if so, we can't match this atom to an element in our list, so the element is unknown
                    if m_n < this_elem['start_range']:
                        # print('unknown', m_n, this_elem['start_range'], this_elem['end_range'], start_index)
                        ABGlobals.element_count['Unknown_n/a'] += 1
                        added += 1
                        break

                    # check if the charge of this atom is greater than the end range of the current element
                    # if so, we increase the start_index when searching in our element list
                    if m_n > this_elem['end_range']:
                        else_counter += 1
                        ABGlobals.element_count['Unknown_n/a'] += 1
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

        print(ABGlobals.element_count)
        print('len:', len(all_atoms))
        print('sum:', sum(ABGlobals.element_count.values()))
        print('else:', else_counter)

        if len(all_atoms) != sum(ABGlobals.element_count.values()):
            raise Exception('#atoms != #element_count')

        print('end atom counting', time.perf_counter() - start)

        ABManagement.init_shader()

    def combine_rrng_and_e_pos_file(self):
        print('both files loaded!')

        point_cloud = bpy.data.objects['Atoms']
        point_cloud.data.attributes.new(name='element', type='INT', domain='POINT')
        point_cloud.data.attributes.new(name='charge', type='FLOAT', domain='POINT')

        # add materials
        for elem in ABGlobals.all_elements:
            name_and_charge = elem['element_name'] + '_' + str(elem['charge'])
            if bpy.data.materials.get(name_and_charge) is None:

                mat = bpy.data.materials.new(name=name_and_charge)
                mat.diffuse_color = elem['color']
                mat.use_nodes = True

                point_cloud.data.materials.append(mat)

        # add material for unknown elements
        unknown_element_mat = bpy.data.materials.new(name='unknown_element')
        unknown_element_mat.diffuse_color = (0.4, 0.4, 0.4, 1.0)
        unknown_element_mat.use_nodes = True
        point_cloud.data.materials.append(unknown_element_mat)

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
        elem_verts['unknown_element'] = [] # atoms that couldn't be matched to an element
        elem_colors = []

        # loop through all the atoms and check all elements if m/n fits the range of this element.
        # as the atoms are sorted by m/n and the elements are also sorted by charge we want
        # to start at the id with the current charge
        vert_count = 0
        start_id = 0
        for v in pc_mn.data:
            element_found = False
            # for elem in ABGlobals.all_elements:
            for i in range(0, len(ABGlobals.all_elements)):
                elem = ABGlobals.all_elements[i]
                start_range = elem['start_range']
                end_range = elem['end_range']
                elem_name = elem['element_name'] + '_' + str(elem['charge'])

                if elem_name not in elem_verts:
                    elem_verts[elem_name] = []

                if v.value >= start_range and v.value <= end_range:
                    element_found = True
                    pos = atom_positions[vert_count]
                    elem_verts[elem_name].append((pos[0], pos[1], pos[2]))
                    # break?

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

            # set material to object
            this_mat = bpy.data.materials[elem_name]
            this_obj = bpy.data.objects[elem_name]
            this_obj.data.materials.append(this_mat)

            for elem in ABGlobals.all_elements:
                elem_and_charge = elem['element_name'] + '_' + str(elem['charge'])
                if elem_and_charge == elem_name:
                    col = elem['color']
                    bpy.data.materials[elem_name].node_tree.nodes["Principled BSDF"].inputs[0].default_value = col

            # create new node group
            modifier = this_elem_object.modifiers.new(elem_name, 'NODES')
            node_group = bpy.data.node_groups.new(type='GeometryNodeTree', name=elem_name)
            modifier.node_group = node_group

            # input node
            group_inputs = node_group.nodes.new('NodeGroupInput')

            # set point radius node
            set_point_radius = node_group.nodes.new('GeometryNodeSetPointRadius')
            set_point_radius.location = (400, 0)
            set_point_radius.inputs[2].default_value = 0.2

            # material node
            # mat = bpy.data.materials[elem_name]
            # set_material_node = node_group.nodes.new('GeometryNodeSetMaterial')
            # set_material_node.inputs[2].default_value = mat
            # set_material_node.location = (600, 0)

            # output node
            group_outputs = node_group.nodes.new('NodeGroupOutput')
            group_outputs.location = (800, 0)
            # node_group.outputs.new('Geometry', 'Output Geometry')

            # link nodes
            node_group.links.new(group_inputs.outputs[0], set_point_radius.inputs[0])
            # node_group.links.new(set_point_radius.outputs[0], set_material_node.inputs[0])
            # node_group.links.new(set_material_node.outputs[0], group_outputs.inputs[0])
            node_group.links.new(set_point_radius.outputs[0], group_outputs.inputs[0])

            # deselect object
            bpy.data.objects[elem_name].select_set(False)

        # we can remove the atoms object as each element has its own object now
        bpy.data.objects.remove(bpy.data.objects['Atoms'], do_unlink=True)


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
        if(ABGlobals.path_rrng == None):
            print('No file loaded')
            return

        # shader preperations
        AtomBlendAddon.rrng_shader_prep(self, context)

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
                elem = splitted_line[3].split(':')
                this_element['element_name'] = elem[0]
                this_element['charge'] = int(elem[1])

                # setting atomic number
                this_element['atomic_number'] = ABGlobals.atomic_numbers[this_element['element_name']]

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

                # add this element to element list
                ABGlobals.all_elements.append(this_element)

                # add this element to element property group to create a color picker in the color settings tab
                elem_name = this_element['element_name'] + '_' + str(this_element['charge'])
                if elem_name not in bpy.context.scene.color_settings:
                    element_color_settings = bpy.context.scene.color_settings.add()
                    element_color_settings.name = elem_name
                    element_color_settings.color = this_element['color']
                    ABGlobals.element_count[elem_name] = 0

        # # add unknown element to all_elements list
        # unknown_element = []
        # unknown_element['name'] = 'Unknown'
        # unknown_element['charge'] = 'n/a'
        # unknown_element['coordinates'] = []
        # ABGlobals.all_elements.append(unknown_element)

        # add property for unknown elements to property group
        element_color_settings = bpy.context.scene.color_settings.add()
        element_color_settings.name = 'Unknown_n/a'
        element_color_settings.color = (0.4, 0.4, 0.4, 1.0)
        ABGlobals.element_count['Unknown_n/a'] = 0

        # sort atoms by start range
        ABGlobals.all_elements.sort(key=lambda x: x.get('start_range'))

        # build all_elements_by_name dict
        for elem in ABGlobals.all_elements:
            name_and_charge = elem['element_name'] + '_' + str(elem['charge'])

            if name_and_charge not in ABGlobals.all_elements_by_name:
                this_element_dict = {}
                print('ELEM', elem)
                this_element_dict['element_name'] = elem['element_name']
                this_element_dict['charge'] = elem['charge']
                this_element_dict['color'] = elem['color']
                this_element_dict['coordinates'] = []
                this_element_dict['num_of_atoms'] = 0
                ABGlobals.all_elements_by_name[name_and_charge] = this_element_dict

        # if both rrng and (e)pos file are loaded, we combine these two files
        if(ABGlobals.FileLoaded_e_pos):
            AtomBlendAddon.combine_rrng_and_e_pos_file_new_new(self, context)


    def load_epos_file(self, context):
        if (ABGlobals.path == None):
            print('No file loaded')
            return

        start = time.perf_counter()
        print('start', start)

        AtomBlendAddon.setup(self, context)

        # file_path = 'T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01.epos'
        file_path = ABGlobals.path

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

        # sort atoms by ['m/n']
        print('sort by m/n')
        sorted_by_mn = concat_data_percentage[concat_data_percentage[:, 3].argsort()]

        ABGlobals.all_data = sorted_by_mn

        print('concat', time.perf_counter() - start)

        # iterate over atoms and add them to coords list
        # for atom in concat_data_percentage:
        #     x = atom[0]
        #     y = atom[1]
        #     z = atom[2]
        #     coords.append((x, y, z))

        coords = [(atom[0], atom[1], atom[2]) for atom in sorted_by_mn]
        print('adding verts', time.perf_counter() - start)

        ABGlobals.atom_coords = coords



        '''
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
        m_n = sorted_by_mn[:, 3:4]
        tof = sorted_by_mn[:, 4:5]
        vspec = sorted_by_mn[:, 5:6]
        vap = sorted_by_mn[:, 6:7]
        xdet = sorted_by_mn[:, 7:8]
        ydet = sorted_by_mn[:, 8:9]
        delta_pulse = sorted_by_mn[:, 9:10]
        ions_pulse = sorted_by_mn[:, 10:11]

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
'''

        # shader experiments !
        # ABGlobals.make_mesh_from_vertices(self)

        print('combine', time.perf_counter() - start)

        # if both rrng and (e)pos file are loaded, we combine these two files
        if(ABGlobals.FileLoadedRRNG):
            AtomBlendAddon.combine_rrng_and_e_pos_file_new_new(self, context)
        else:
            AtomBlendAddon.e_pos_shader_prep(self, context)

        print('end', time.perf_counter() - start)


    def load_pos_file(self, context):
        if (ABGlobals.path == None):
            print('No file loaded')
            return

        AtomBlendAddon.setup(self, context)

        # file_path = 'T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01.epos'
        file_path = ABGlobals.path
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

        # sort atoms by ['m/n']
        print('sort by m/n')
        sorted_by_mn = reshaped_data_percentage[reshaped_data_percentage[:, 3].argsort()]

        ABGlobals.all_data = sorted_by_mn

        coords = [(atom[0], atom[1], atom[2]) for atom in reshaped_data_percentage]
        ABGlobals.atom_coords = coords

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
        if (ABGlobals.FileLoadedRRNG):
            AtomBlendAddon.combine_rrng_and_e_pos_file_new_new(self, context)
        else:
            AtomBlendAddon.e_pos_shader_prep(self, context)
