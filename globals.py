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

    path: str = None

    def load_epos_file(self):
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

        for atom in concat_data:
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
        m_n = concat_data[:, 3:4]
        tof = concat_data[:, 4:5]
        vspec = concat_data[:, 5:6]
        vap = concat_data[:, 6:7]
        xdet = concat_data[:, 7:8]
        ydet = concat_data[:, 8:9]
        delta_pulse = concat_data[:, 9:10]
        ions_pulse = concat_data[:, 10:11]

        # set attribute values in point_cloud
        point_cloud.data.attributes['m/n'].data.foreach_set('value', m_n.ravel())
        point_cloud.data.attributes['TOF'].data.foreach_set('value', tof.ravel())
        point_cloud.data.attributes['Vspec'].data.foreach_set('value', vspec.ravel())
        point_cloud.data.attributes['Vap'].data.foreach_set('value', vap.ravel())
        point_cloud.data.attributes['xdet'].data.foreach_set('value', xdet.ravel())
        point_cloud.data.attributes['ydet'].data.foreach_set('value', ydet.ravel())
        point_cloud.data.attributes['delta pulse'].data.foreach_set('value', delta_pulse.ravel())
        point_cloud.data.attributes['ions/pulse'].data.foreach_set('value', ions_pulse.ravel())

    def load_pos_file(self):
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

        for atom in reshaped_data:
            # generate points with x, y, z values
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
        m_n = reshaped_data[:, 3:4]

        # set attribute values in point_cloud
        point_cloud.data.attributes['m/n'].data.foreach_set('value', m_n)

    # @staticmethod
    # def setup_scene():
    #     print('SETTING UP SCENE')
    #     # import the file from the given path
    #     if (AtomBlendAddon.path == None):
    #         print("No file loaded")
    #         return
    #
    #     # set the origin so everything moves in relation to eachother and the bounding boxes are in world coordinates
    #     bpy.context.scene.cursor.location = [0, 0, 0]
    #     bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    #     bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


