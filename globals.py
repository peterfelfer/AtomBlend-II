import bpy
import os

class ABGlobals:
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
    FileLoaded_rrng = False

    path: str = None
    path_rrng: str = None
    dataset_name = None

    # atom data
    all_elements = []
    all_elements_by_name = {}  # dict with all the elements, every element has a list with all its ranges
    all_data = []
    #atomic_numbers = []
    element_count = {}  # counts the amount of each element to pass the correct amount of colors to the shader later
    atom_coords = []
    unknown_label = 'n/a_n/a'
    max_x = 0
    min_x = 0
    max_y = 0
    min_y = 0
    max_z = 0
    min_z = 0

    # atom appearance
    atom_color_list = []
    point_size_list = []
    point_size = 5.0

    # booleans for operators
    render_frame = True  # if True, we render a picture, if False, we render a video
    animation_playing = False
    currently_writing_img = False