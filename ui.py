import bpy

from .read_data import *

# ------------------- EXTERNAL MODULES -------------------
import sys
from math import *

import bpy
from bpy.props import StringProperty
from bpy.types import PropertyGroup

import numpy as np

# append the add-on's path to Blender's python PATH
sys.path.insert(0, AtomBlendAddon.addon_path)


# ------------- Add-on UI -------------
# Class that contains all functions relevant for the UI
class AtomBlendAddonUI:
    def update_vertex_percentage(self, context):
        print('SELECT VERTEX PERCENTAGE')

# Preferences panel for this Addon in the Blender preferences
class AtomBlendAddonSettings(bpy.types.PropertyGroup):
    vertex_percentage: bpy.props.FloatProperty(
        name="Atoms shown",
        default=0.01,
        min=0.0001,
        max=100,
        soft_min=1,
        step=10,
        description="Percentage of atoms shown",
        subtype='PERCENTAGE',
        update=AtomBlendAddonUI.update_vertex_percentage,
        precision=3
    )

    stuff = {}


    material_settings: bpy.props.FloatVectorProperty(
        name="Material",
        min=0.0,
        max=1.0,
        subtype="COLOR",
        size=4,
        # update=AtomBlendAddonUI.update_background,
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

class ATOMBLEND_PT_panel_rrng_file(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_panel_rrng_file"  # unique identifier for buttons and menu items to reference.
    bl_label = "Load .rrng file"  # display name in the interface.
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
        col = layout.column(align=True)
        load_file_row = col.row(align=True)
        load_file_row.operator('atom_blend_viewer.load_rrng_file', text="Load file", icon="FILE_FOLDER")

        loaded_row = col.row()
        if AtomBlendAddon.FileLoadedRRNG:
            loaded_row.label(text='Loaded File: ' + AtomBlendAddon.path_rrng)
        else:
            loaded_row.label(text='No file loaded yet...')

        col.row(align=True)

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
        col = layout.column(align=True)
        vertex_percentage_row = col.row()
        vertex_percentage_row.prop(context.scene.atom_blend_addon_settings, "vertex_percentage")

        load_file_row = col.row()
        load_file_row.operator('atom_blend_viewer.load_file', text="Load file", icon="FILE_FOLDER")

        loaded_row = col.row()
        if AtomBlendAddon.FileLoaded_e_pos:
            loaded_row.label(text='Loaded File: ' + AtomBlendAddon.path)
        else:
            loaded_row.label(text='No file loaded yet...')

        col.row(align=True)


class UElementPropertyGroup(bpy.types.PropertyGroup):
    s = StringProperty(default="UElement")
    print('ue element prop group')

class MaterialSetting(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Test Property", default="Unknown")
    value: bpy.props.FloatVectorProperty(name="Test Property")

    # bpy.types.Scene.my_settings = bpy.props.CollectionProperty(type=UElementPropertyGroup)

    # list = bpy.props.CollectionProperty(type=MaterialSetting)
    print('mat settings')
    # print('list: ', list)
    # def fill_to(self):
    # list.add()
    print('fill to')


class ATOMBLEND_PT_color_settings(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_color_settings"  # unique identifier for buttons and menu items to reference.
    bl_label = "Color settings"  # display name in the interface.
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    bl_parent_id = "ATOMBLEND_PT_panel_general"

    @classmethod
    def poll(cls, context):
        return True  # context.object is not None

    bpy.types.Object.material_settings = bpy.props.FloatVectorProperty(
        name="Material",
        min=0.0,
        max=1.0,
        subtype="COLOR",
        size=4,
        # update=AtomBlendAddonUI.update_background,
    )

    def draw(self, context):
        print('hello')
        layout = self.layout
        # only draw if both files are loaded
        # ll = bpy.props.CollectionProperty(type=MaterialSetting)
        # ll.add()
        # box = layout.box()
        # element_row = box.row()


        # element_row.prop(context.scene.my_settings, 'material_settings')

        AtomBlendAddonSettings.stuff['test'] = bpy.props.FloatVectorProperty(
            name="Material",
            min=0.0,
            max=1.0,
            subtype="COLOR",
            size=4,
            # update=AtomBlendAddonUI.update_background,
        )

        # element_row.prop(self, 'material_settings')
        if AtomBlendAddon.FileLoadedRRNG and AtomBlendAddon.FileLoaded_e_pos:
            # context.scene.my_settings = CollectionProperty(type=MaterialSetting)

            # my_item = bpy.context.scene.my_settings.add()
            # my_item.name = "Spam"
            # my_item.value = (1.0, 0.0, 0.0, 1.0)

            # make one top row for labeling

            col = layout.column(align=True)
            row = col.row(align=True)
            # row = col.row(align=True)
            name_col = row.column(align=True)
            charge_col = row.column(align=True)
            color_col = row.column(align=True)

            name_col.label(text='Name')
            charge_col.label(text='Charge')
            color_col.label(text='Color')

            col.separator()

            for obj in bpy.data.objects:
                print(obj)
                obj_mats = [m.material for m in obj.material_slots]
                for mat in obj_mats:
                    print(mat)
                    # mat = obj.material_slots[0].material
                    # if len(obj.material_slots) < 1:
                    #     print('mat slots < 1')

                    # add unknown element at the end because elements are stored alphabetically
                    if mat.name == 'unknown_element':
                        continue

                    if mat and mat.use_nodes:
                        print(mat)
                        bsdf = mat.node_tree.nodes.get("Principled BSDF")
                        row = col.row(align=True)
                        name_col = row.column(align=True)
                        charge_col = row.column(align=True)
                        color_col = row.column(align=True)

                        splitted_name = mat.name.split('_')

                        print(splitted_name)

                        name_col.label(text=splitted_name[0])
                        charge_col.label(text=splitted_name[1])

                        color_col.prop(bsdf.inputs['Base Color'], "default_value", text='')

            # add unknown element to the end of the list
            mat = bpy.data.objects['unknown_element'].material_slots[0].material
            if mat and mat.use_nodes:
                bsdf = mat.node_tree.nodes.get("Principled BSDF")
                row = col.row(align=True)
                name_col = row.column(align=True)
                charge_col = row.column(align=True)
                color_col = row.column(align=True)

                name_col.label(text='Unknown')
                charge_col.label(text='?')
                color_col.prop(bsdf.inputs['Base Color'], "default_value", text='')

                # AtomBlendAddon.all_elements[mat.name]
                # bpy.data.materials["Fe_1"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (1.0, 0.0, 0.0, 1)

            # for elem in AtomBlendAddon.all_elements:
            #     # define a box of UI elements
            #     box = layout.box()
            #     element_row = box.row()

                # my_item = bpy.context.material.my_settings.add()
                # my_item.name = "Spam"
                # my_item.value = (1.0, 0.0, 0.0, 1.0)

                # print(elem)
                # material_settings: bpy.props.FloatVectorProperty(
                #     name="Material",
                #     min=0.0,
                #     max=1.0,
                #     subtype="COLOR",
                #     size=4,
                #     # update=AtomBlendAddonUI.update_background,
                # )

                # element_row.prop(context.object, 'material_settings')

                # element_row.prop(context.scene.atom_blend_addon_settings, 'material_settings')
                # context.scene.atom_blend_addon_settings.vertex_percentage.name = 'x'
                # AtomBlendAddonSettings.material_settings.name = 'x'
        else:
            col = layout.column(align=True)
            text_row = col.row()
            text_row.label(text='Load .epos/.pos and .rrng file')


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
        if AtomBlendAddon.FileLoaded_e_pos:
            obj_to_delete = bpy.data.objects['Atoms']
            bpy.data.objects.remove(obj_to_delete, do_unlink=True)

            # removing geometry nodes group
            geometry_nodes_group = bpy.data.node_groups['Geometry Nodes']
            bpy.data.node_groups.remove(geometry_nodes_group)

        if AtomBlendAddon.path.lower().endswith('.epos'):
            AtomBlendAddon.load_epos_file(self, context)
        elif AtomBlendAddon.path.lower().endswith('.pos'):
            AtomBlendAddon.load_pos_file(self, context)

        AtomBlendAddon.FileLoaded_e_pos = True
        print(f"Object Loaded: {AtomBlendAddon.FileLoaded_e_pos}")

        # print(bpy.data.screens["Modeling-nonnormal"].shading.type)

        # bpy.data.screens["Modeling-nonnormal"].shading.type = "RENDERED"

        # bpy.ops.view3d.toggle_shading(type='RENDERED')

        # https://docs.blender.org/api/current/bpy.types.Operator.html#calling-a-file-selector
        return {'FINISHED'}

    def invoke(self, context, event):
        print("the selected filepath" + self.filepath)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class ATOMBLEND_OT_load_rrng_file(bpy.types.Operator):
    bl_idname = "atom_blend_viewer.load_rrng_file"
    bl_label = "Open file"
    bl_description = "Load a file of the following types:\n.rrng"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(
        default='*.rrng',
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        return True  # context.object is not None

    def execute(self, context):
        print("the selected filepath" + self.filepath)
        AtomBlendAddon.path_rrng = self.filepath
        # AtomBlendAddon.setup_scene()


        if AtomBlendAddon.path_rrng.lower().endswith('.rrng'):
            AtomBlendAddon.load_rrng_file(self, context)

        AtomBlendAddon.FileLoadedRRNG = True
        print(f"Object Loaded: {AtomBlendAddon.FileLoadedRRNG}")

        # https://docs.blender.org/api/current/bpy.types.Operator.html#calling-a-file-selector
        return {'FINISHED'}

    def invoke(self, context, event):
        print("the selected filepath" + self.filepath)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

