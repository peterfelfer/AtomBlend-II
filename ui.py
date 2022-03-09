import bpy

from .globals import *

# ------------------- EXTERNAL MODULES -------------------
import sys
from math import *

import bpy
from bpy.props import FloatProperty, PointerProperty
from bpy.types import PropertyGroup

import numpy as np

# append the add-on's path to Blender's python PATH
sys.path.insert(0, AtomBlendAddon.addon_path)


# ------------- Add-on UI -------------
# Class that contains all functions relevant for the UI
class AtomBlendAddonUI:
    def update_background(self, context):
        print("BACKGOUND_COLOR")
        bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = context.scene.holo_addon_settings.background_color
        bpy.data.scenes["Scene"].node_tree.nodes["RGB"].outputs[0].default_value = context.scene.holo_addon_settings.background_color
        return None


# Preferences pane for this Addon in the Blender preferences
class AtomBlendAddonSettings(bpy.types.PropertyGroup):
    background_color: bpy.props.FloatVectorProperty(
        name="Background Color",
        min=0.0,
        max=1.0,
        subtype="COLOR",
        size=4,
        update=AtomBlendAddonUI.update_background,
    )


class ATOMBLEND_PT_panel_general(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_panel_general"  # unique identifier for buttons and menu items to reference.
    bl_label = "AtomBlend-II"  # display name in the interface.
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"

    # @classmethod
    # def poll(cls, context):
    #     # the panel should always be drawn
    #     return True

    def draw(self, context):
        layout = self.layout
        column = layout.column()
        column.label(text=".epos file")


class ATOMBLEND_PT_panel_file(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_panel_file"  # unique identifier for buttons and menu items to reference.
    bl_label = "Load file"  # display name in the interface.
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    bl_parent_id = "ATOMBLEND_PT_panel_general"

    # define own poll method to be able to hide / show the panel on demand
    @classmethod
    def poll(cls, context):
        # the panel should always be drawn
        return True

    def draw(self, context):
        layout = self.layout

        # define a column of UI elements
        column = layout.column(align=True)

        row_load_object_btn = column.row(align=True)
        row_load_object_btn.operator('atom_blend_viewer.load_file', text="Load .epos file", icon="FILE_FOLDER")
        loaded_row = column.row(align=True)
        if AtomBlendAddon.FileLoaded:
            loaded_row.label(text='Loaded File: ' + AtomBlendAddon.path)
        else:
            loaded_row.label(text='No file loaded yet...')


# Operators used for buttons
class ATOMBLEND_OT_load_file(bpy.types.Operator):
    bl_idname = "atom_blend_viewer.load_file"
    bl_label = "Open file"
    bl_description = "Load a file of the following types:\n.epos"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(
        default='*.epos',
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        return True  # context.object is not None

    def execute(self, context):
        print("the selected filepath" + self.filepath)
        AtomBlendAddon.path = self.filepath
        # AtomBlendAddon.setup_scene()

        AtomBlendAddon.load_epos_file()

        AtomBlendAddon.FileLoaded = True
        # TODO: wanna catch if someone deletes the object
        print(f"Object Loaded: {AtomBlendAddon.FileLoaded}")

        # print(bpy.data.screens["Modeling-nonnormal"].shading.type)

        # bpy.data.screens["Modeling-nonnormal"].shading.type = "RENDERED"

        bpy.ops.view3d.toggle_shading(type='RENDERED')

        # https://docs.blender.org/api/current/bpy.types.Operator.html#calling-a-file-selector
        return {'FINISHED'}

    def invoke(self, context, event):
        print("the selected filepath" + self.filepath)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
