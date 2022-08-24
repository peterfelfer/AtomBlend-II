# -------------------- DEFINE ADDON ----------------------
bl_info = {
    "name": "AtomBlend-II",
    "author": "Juliane Reithmeier",
    "version": (1, 0, 0),
    "blender": (3, 0, 1),
    #"location": "",
    "description": "AtomBlend-II",
    "category": "View",
    "warning": "",
    "doc_url": "",
}

########################################################
#              Prepare Add-on Initialization
########################################################

# Load System Modules
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++
import sys

########################################################
#                  Add-on Initialization
########################################################
import bpy
from bpy.types import AddonPreferences
from bpy.app.handlers import persistent

from .read_data import *
from .ui import *
from .atomic_numbers import *
from .shader_management import ABManagement
from .globals import ABGlobals

# ------------- LOAD INTERNAL MODULES ----------------
# append the add-on's path to Blender's python PATH
sys.path.insert(0, ABGlobals.addon_path)

# define add-on name for display purposes
ABGlobals.name = bl_info['name'] + " v" + '.'.join(str(v) for v in bl_info['version'])

# set atomic number dict
ABGlobals.atomic_numbers = atomic_numbers.atomic_numbers_dict

# Check Blender Version
# +++++++++++++++++++++++++++++++++++++++++++++
# check, if a supported version of Blender is executed
if bpy.app.version < bl_info['blender']:
    raise Exception("This version of Blender is not supported by " + bl_info['name'] + ". Please use v" + '.'.join(str(v) for v in bl_info['blender']) + " or higher.")


# ----------------- ADDON INITIALIZATION --------------------
@persistent
def atom_blend_addon_init_handler(dummy1, dummy2):
    # load the panel variables
    bpy.types.Scene.atom_blend_addon_settings = bpy.props.PointerProperty(type=AB_properties)

    # my_item = bpy.context.scene.my_settings.add()
    # my_item.name = "Spam"
    # my_item.value = 1000
    #
    # my_item = bpy.context.scene.my_settings.add()
    # my_item.name = "Eggs"
    # my_item.value = 30

    # get the active window
    AtomBlendAddon.BlenderWindow = bpy.context.window


    # cube1_item = bpy.context.scene.my_settings.add()
    # cube1_item.name = 'Cube1'
    # cube1_item.value = 100


# ---------- ADDON INITIALIZATION & CLEANUP -------------
def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.app.handlers.load_post.append(atom_blend_addon_init_handler)
    bpy.app.handlers.frame_change_pre.append(ABManagement.handler)
    bpy.app.handlers.render_pre.append(ABManagement.handler)

    bpy.types.Scene.color_settings = bpy.props.CollectionProperty(type=DisplaySettings)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    # remove initialization helper app handler
    bpy.app.handlers.load_post.remove(atom_blend_addon_init_handler)
    bpy.app.handlers.frame_change_pre.remove(ABManagement.handler)
    bpy.app.handlers.render_pre.remove(ABManagement.handler)

    # UI elements
    for c in reversed(classes):
        if hasattr(bpy.types, str(c)): bpy.utils.unregister_class(c)


classes = (
    AB_properties, DisplaySettings,

    ATOMBLEND_PT_panel_general, ATOMBLEND_PT_panel_dev, ATOMBLEND_PT_panel_file,
    ATOMBLEND_PT_shader_display_settings, ATOMBLEND_PT_rendering, ATOMBLEND_OT_preview,
    ATOMBLEND_OT_load_file, ATOMBLEND_OT_load_rrng_file, ATOMBLEND_OT_render, ATOMBLEND_OT_render_frame,
    ATOMBLEND_OT_render_video, ATOMBLEND_OT_start_stop,
)

# # this should only be needed if we want to start the addon with the play button from within blender
# if __name__ == "__main__":
#     register()
