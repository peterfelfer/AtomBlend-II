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
    FileLoaded = False
    FileLoadedRRNG = False

    path: str = None
    path_rrng: str = None

    def make_mesh_from_vertices(self):
        ### visualize every vertex we have as mesh (currently: icosphere)
        # make new node group
        bpy.ops.node.new_geometry_nodes_modifier()
        geometry_nodes_group = bpy.data.node_groups['Geometry Nodes']

        # add new nodes
        input_node = geometry_nodes_group.nodes['Group Input']
        output_node = geometry_nodes_group.nodes['Group Output']
        iop_node = geometry_nodes_group.nodes.new(type='GeometryNodeInstanceOnPoints')
        mesh_node = geometry_nodes_group.nodes.new(type='GeometryNodeMeshIcoSphere')
        mesh_node.location = (-300, -100)
        mesh_node.inputs[0].default_value = 0.3

        # link nodes
        geometry_nodes_group.links.new(input_node.outputs[0], iop_node.inputs[0])
        geometry_nodes_group.links.new(mesh_node.outputs[0], iop_node.inputs[2])
        geometry_nodes_group.links.new(iop_node.outputs[0], output_node.inputs[0])


    def load_rrng_file(self, context):
        print('LOADING .RRNG FILE')
        if(AtomBlendAddon.path_rrng == None):
            print('No file loaded')
            return

        file_path = AtomBlendAddon.path_rrng

    def load_epos_file(self, context):
        print('LOADING .EPOS FILE')
        if (AtomBlendAddon.path == None):
            print('No file loaded')
            return

        # file_path = 'T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01.epos'
        file_path = AtomBlendAddon.path

        # reading the given binary file and store it into a numpy array
        # reading data as byte representation in float and int (as the last two values are ints we need a integer representation as well)
        data_in_bytes_float = np.fromfile(file_path, dtype='>f')
        data_in_bytes_int = np.fromfile(file_path, dtype='>i')
        print(data_in_bytes_float[0:11])
        print(data_in_bytes_int[0:11])

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

        # creating the mesh in blender
        # create a new mesh and a new object
        mesh = bpy.data.meshes.new("point-cloud")  # add a new mesh
        point_cloud = bpy.data.objects.new("Atoms", mesh)  # add a new object using the mesh

        # iterate over atoms and add them to coords list
        coords = []
        edges = []
        faces = []

        # reducing the atom data by a certain percentage by only taking the first n elements
        atoms_percentage = context.scene.atom_blend_addon_settings.vertex_percentage / 100

        # shuffling the data as they're kind of sorted by the z value
        # TODO: is shuffling the data a problem?
        np.random.shuffle(concat_data)

        num_of_atoms_percentage = int(num_of_atoms * atoms_percentage)
        # print(num_of_atoms, num_of_atoms_percentage)
        concat_data_percentage = concat_data[:num_of_atoms_percentage]

        for atom in concat_data_percentage:
            x = atom[0]
            y = atom[1]
            z = atom[2]
            coords.append((x, y, z))

        # Make a mesh from a list of vertices/edges/faces
        mesh.from_pydata(coords, edges, faces)

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
        point_cloud.data.attributes.new(name='delta pulse', type='INT', domain='POINT')
        point_cloud.data.attributes.new(name='ions/pulse', type='INT', domain='POINT')

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
        point_cloud.data.attributes['TOF'].data.foreach_set('value', tof.ravel())
        point_cloud.data.attributes['Vspec'].data.foreach_set('value', vspec.ravel())
        point_cloud.data.attributes['Vap'].data.foreach_set('value', vap.ravel())
        point_cloud.data.attributes['xdet'].data.foreach_set('value', xdet.ravel())
        point_cloud.data.attributes['ydet'].data.foreach_set('value', ydet.ravel())
        point_cloud.data.attributes['delta pulse'].data.foreach_set('value', delta_pulse.ravel())
        point_cloud.data.attributes['ions/pulse'].data.foreach_set('value', ions_pulse.ravel())

        AtomBlendAddon.make_mesh_from_vertices(self)

    def load_pos_file(self, context):
        print('LOADING .POS FILE')
        if (AtomBlendAddon.path == None):
            print('No file loaded')
            return

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

        # iterate over atoms and add them to coords list
        coords = []
        edges = []
        faces = []

        # reducing the atom data by a certain percentage by only taking the first n elements
        atoms_percentage = context.scene.atom_blend_addon_settings.vertex_percentage / 100

        # shuffling the data as they're kind of sorted by the z value
        # TODO: is shuffling the data a problem?
        np.random.shuffle(reshaped_data)

        num_of_atoms_percentage = int(num_of_atoms * atoms_percentage)
        # print(num_of_atoms, num_of_atoms_percentage)
        reshaped_data_percentage = reshaped_data[:num_of_atoms_percentage]

        for atom in reshaped_data_percentage:
            x = atom[0]
            y = atom[1]
            z = atom[2]
            coords.append((x, y, z))

        # Make a mesh from a list of vertices/edges/faces
        mesh.from_pydata(coords, edges, faces)

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