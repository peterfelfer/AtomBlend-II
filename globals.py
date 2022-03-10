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
        print('SHAPE: ', concat_data)

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


        # scene = bpy.context.scene
        # scene.objects.link(point_cloud)  # put the object into the scene (link)
        # scene.objects.active = point_cloud  # set as the active object in the scene
        # point_cloud.select = True  # select object

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


