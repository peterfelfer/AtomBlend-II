# -------------------- DEFINE ADDON ----------------------
bl_info = {
    "name": "AtomBlend-II",
    "author": "Juliane Reithmeier",
    "version": (1, 0, 0),
    "blender": (3, 5, 0),
    "description": "Display and edit data from atom tips and render images or videos of your science",
    "category": "View",
    "warning": "",
    "doc_url": "",
    "location": "View3D > Sidebar > AtomBlend-II",
    "tracker_url": "https://github.com/peterfelfer/AtomBlend-II/issues",
    "wiki_url": "https://github.com/peterfelfer/AtomBlend-II",
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
#from .atomic_numbers import *
from .shader_management import ABManagement
from .globals import ABGlobals
from .gaussian_splatting_renderer import CustomRenderEngine

# ------------- LOAD INTERNAL MODULES ----------------
# append the add-on's path to Blender's python PATH
sys.path.insert(0, ABGlobals.addon_path)

# define add-on name for display purposes
ABGlobals.name = bl_info['name'] + " v" + '.'.join(str(v) for v in bl_info['version'])

# check, if a supported version of Blender is executed
if bpy.app.version < bl_info['blender']:
    raise Exception("This version of Blender is not supported by " + bl_info['name'] + ". Please use v" + '.'.join(str(v) for v in bl_info['blender']) + " or higher.")

# ---------- ADDON INITIALIZATION & CLEANUP -------------
def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.atom_blend_addon_settings = bpy.props.PointerProperty(type=AB_properties)

    bpy.app.handlers.render_pre.append(ABManagement.handler)

    bpy.types.Scene.color_settings = bpy.props.CollectionProperty(type=DisplaySettings)
    bpy.types.Scene.color_settings_pointer = bpy.props.PointerProperty(type=DisplaySettings)

    for panel in get_panels():
        panel.COMPAT_ENGINES.add('GAUSSIAN_SPLATTING_RENDERER')

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    #bpy.app.handlers.render_pre.remove(ABManagement.handler)

    # UI elements
    for c in reversed(classes):
        if hasattr(bpy.types, str(c)): bpy.utils.unregister_class(c)

    for panel in get_panels():
        if 'GAUSSIAN_SPLATTING_RENDERER' in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.remove('GAUSSIAN_SPLATTING_RENDERER')

# RenderEngines also need to tell UI Panels that they are compatible with.
# We recommend to enable all panels marked as BLENDER_RENDER, and then
# exclude any panels that are replaced by custom panels registered by the
# render engine, or that are not supported.
def get_panels():
    exclude_panels = {
        'VIEWLAYER_PT_filter',
        'VIEWLAYER_PT_layer_passes',
    }

    panels = []
    for panel in bpy.types.Panel.__subclasses__():
        if hasattr(panel, 'COMPAT_ENGINES') and 'BLENDER_RENDER' in panel.COMPAT_ENGINES:
            if panel.__name__ not in exclude_panels:
                panels.append(panel)

    return panels

classes = (
    AB_properties, DisplaySettings,

    #ATOMBLEND_PT_panel_general, #ATOMBLEND_PT_panel_dev,
    ATOMBLEND_PT_panel_file, ATOMBLEND_PT_gaussian_splatting, ATOMBLEND_PT_shader_display_settings, ATOMBLEND_PT_scaling_cube, ATOMBLEND_PT_scaling_cube_track_to_center,
    ATOMBLEND_PT_legend_basic, ATOMBLEND_PT_legend_advanced_settings, ATOMBLEND_PT_placement_settings, ATOMBLEND_PT_camera_settings_track_to_center,
    ATOMBLEND_PT_rendering,

    ATOMBLEND_OT_preview, ATOMBLEND_OT_load_file, ATOMBLEND_OT_load_rrng_file, ATOMBLEND_OT_render, ATOMBLEND_OT_render_frame,
    ATOMBLEND_OT_render_video, ATOMBLEND_OT_start_stop, ATOMBLEND_OT_unload_files,

    CustomRenderEngine,
)