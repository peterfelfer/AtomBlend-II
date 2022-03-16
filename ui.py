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
    def update_vertex_percentage(self, context):
        print('SELECT VERTEX PERCENTAGE')



# Preferences pane for this Addon in the Blender preferences
class AtomBlendAddonSettings(bpy.types.PropertyGroup):
    vertex_percentage: bpy.props.IntProperty(
        name="Atoms shown",
        default=10,
        min=1,
        max=100,
        soft_min=1,
        step=10,
        description="Percentage of atoms shown",
        subtype='PERCENTAGE',
        update=AtomBlendAddonUI.update_vertex_percentage,
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
        # column.label(text=".epos file")


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

        # define a box of UI elements
        box = layout.box()
        vertex_percentage_row = box.row()
        vertex_percentage_row.prop(context.scene.atom_blend_addon_settings, "vertex_percentage")

        load_file_row = box.row()
        load_file_row.operator('atom_blend_viewer.load_file', text="Load file", icon="FILE_FOLDER")

        loaded_row = box.row()
        if AtomBlendAddon.FileLoaded:
            loaded_row.label(text='Loaded File: ' + AtomBlendAddon.path)
        else:
            loaded_row.label(text='No file loaded yet...')


# Operators used for buttons
class ATOMBLEND_OT_load_file(bpy.types.Operator):
    bl_idname = "atom_blend_viewer.load_file"
    bl_label = "Open file"
    bl_description = "Load a file of the following types:\n.epos, .pos"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(
        default='*.epos;*.pos',
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        return True  # context.object is not None

    def execute(self, context):
        print("the selected filepath" + self.filepath)
        AtomBlendAddon.path = self.filepath
        # AtomBlendAddon.setup_scene()

        # if there's already an object loaded we want to delete it so we can load another object
        if AtomBlendAddon.FileLoaded:
            obj_to_delte = bpy.data.objects['Atoms']
            bpy.data.objects.remove(obj_to_delte, do_unlink=True)

        if AtomBlendAddon.path.endswith('.epos'):
            AtomBlendAddon.load_epos_file(self, context)
        elif AtomBlendAddon.path.endswith('.pos'):
            AtomBlendAddon.load_pos_file(self, context)

        AtomBlendAddon.FileLoaded = True
        print(f"Object Loaded: {AtomBlendAddon.FileLoaded}")

        # print(bpy.data.screens["Modeling-nonnormal"].shading.type)

        # bpy.data.screens["Modeling-nonnormal"].shading.type = "RENDERED"

        # bpy.ops.view3d.toggle_shading(type='RENDERED')

        # https://docs.blender.org/api/current/bpy.types.Operator.html#calling-a-file-selector
        return {'FINISHED'}

    def invoke(self, context, event):
        print("the selected filepath" + self.filepath)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}