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

    def load_epos_file():
        print('LOADING .EPOS FILE')

        if(AtomBlendAddon.path == None):
            print('No file loaded')
            return

        # reading a .epos input file and converting it to float values
        file_path = 'T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01.epos'
        data_in_bytes = np.fromfile(AtomBlendAddon.path, dtype='uint8')
        data_as_float = data_in_bytes.view(dtype=np.float32)

        # calculating how many atoms we have as input; dividing by 11 because there are 11 features to store
        num_of_atoms = int(data_as_float.shape[0] / 11)
        reshaped_data = np.reshape(data_as_float, (num_of_atoms, 11))
        print('SHAPE: ', reshaped_data.shape)



    @staticmethod
    def setup_scene():
        print('SETTING UP SCENE')
        # import the file from the given path
        if (AtomBlendAddon.path == None):
            print("No file loaded")
            return

        # set the origin so everything moves in relation to eachother and the bounding boxes are in world coordinates
        bpy.context.scene.cursor.location = [0, 0, 0]
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


