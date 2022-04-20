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

from AtomBlend.read_data import *
from AtomBlend.ui import *
from AtomBlend.atomic_numbers import *

# ------------- LOAD INTERNAL MODULES ----------------
# append the add-on's path to Blender's python PATH
sys.path.insert(0, AtomBlendAddon.addon_path)

# define add-on name for display purposes
AtomBlendAddon.name = bl_info['name'] + " v" + '.'.join(str(v) for v in bl_info['version'])

# set atomic number dict
AtomBlendAddon.atomic_numbers = AtomBlend.atomic_numbers_dict

# Check Blender Version
# +++++++++++++++++++++++++++++++++++++++++++++
# check, if a supported version of Blender is executed
if bpy.app.version < bl_info['blender']:
    raise Exception("This version of Blender is not supported by " + bl_info['name'] + ". Please use v" + '.'.join(str(v) for v in bl_info['blender']) + " or higher.")

# ----------------- ADDON INITIALIZATION --------------------
@persistent
def atom_blend_addon_init_handler(dummy1, dummy2):
    # load the panel variables
    bpy.types.Scene.atom_blend_addon_settings = bpy.props.PointerProperty(type=AtomBlendAddonSettings)

    # get the active window
    AtomBlendAddon.BlenderWindow = bpy.context.window

# ---------- ADDON INITIALIZATION & CLEANUP -------------
def register():
    # register all basic operators of the addon
    bpy.utils.register_class(AtomBlendAddonSettings)
    # bpy.utils.register_class(AtomBlendAddonUI)
    bpy.utils.register_class(ATOMBLEND_OT_load_file)
    bpy.utils.register_class(ATOMBLEND_OT_load_rrng_file)

    # UI elements
    # add-on panels
    bpy.utils.register_class(ATOMBLEND_PT_panel_general)
    bpy.utils.register_class(ATOMBLEND_PT_panel_file)
    bpy.utils.register_class(ATOMBLEND_PT_panel_rrng_file)

    bpy.app.handlers.load_post.append(atom_blend_addon_init_handler)

def unregister():
    # unregister all classes of the addon
    bpy.utils.unregister_class(AtomBlendAddonSettings)
    # bpy.utils.unregister_class(AtomBlendAddonUI)
    bpy.utils.unregister_class(ATOMBLEND_OT_load_file)
    bpy.utils.unregister_class(ATOMBLEND_OT_load_rrng_file)

    # remove initialization helper app handler
    bpy.app.handlers.load_post.remove(atom_blend_addon_init_handler)

    # UI elements
    if hasattr(bpy.types, "ATOMBLEND_PT_panel_general"): bpy.utils.unregister_class(ATOMBLEND_PT_panel_general)
    if hasattr(bpy.types, "ATOMBLEND_PT_panel_file"): bpy.utils.unregister_class(ATOMBLEND_PT_panel_file)
    if hasattr(bpy.types, "ATOMBLEND_PT_panel_file"): bpy.utils.unregister_class(ATOMBLEND_PT_panel_rrng_file)
    # delete all variables
    if hasattr(bpy.types.Scene, "holo_addon_settings"): del bpy.types.Scene.holo_addon_settings

# this should only be needed if we want to start the addon with the play button from within blender
if __name__ == "__main__":
    register()
