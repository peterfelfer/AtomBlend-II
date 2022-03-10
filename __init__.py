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

from AtomBlend.globals import *
from AtomBlend.ui import *

# ------------- LOAD INTERNAL MODULES ----------------
# append the add-on's path to Blender's python PATH
sys.path.insert(0, AtomBlendAddon.addon_path)

# define add-on name for display purposes
AtomBlendAddon.name = bl_info['name'] + " v" + '.'.join(str(v) for v in bl_info['version'])

# Check Blender Version
# +++++++++++++++++++++++++++++++++++++++++++++
# check, if a supported version of Blender is executed
if bpy.app.version < bl_info['blender']:
    raise Exception("This version of Blender is not supported by " + bl_info['name'] + ". Please use v" + '.'.join(str(v) for v in bl_info['blender']) + " or higher.")


# ---------- ADDON INITIALIZATION & CLEANUP -------------
def register():
    # register all basic operators of the addon
    bpy.utils.register_class(AtomBlendAddonSettings)
    # bpy.utils.register_class(AtomBlendAddonUI)
    bpy.utils.register_class(ATOMBLEND_OT_load_file)

    # UI elements
    # add-on panels
    bpy.utils.register_class(ATOMBLEND_PT_panel_general)
    bpy.utils.register_class(ATOMBLEND_PT_panel_file)


def unregister():
    # unregister all classes of the addon
    bpy.utils.unregister_class(AtomBlendAddonSettings)
    # bpy.utils.unregister_class(AtomBlendAddonUI)
    bpy.utils.unregister_class(ATOMBLEND_OT_load_file)

    # UI elements
    if hasattr(bpy.types, "ATOMBLEND_PT_panel_general"): bpy.utils.unregister_class(ATOMBLEND_PT_panel_general)
    if hasattr(bpy.types, "ATOMBLEND_PT_panel_file"): bpy.utils.unregister_class(ATOMBLEND_PT_panel_file)

# this should only be needed if we want to start the addon with the play button from within blender
if __name__ == "__main__":
    register()
