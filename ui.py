import bpy

from .read_data import *

# ------------------- EXTERNAL MODULES -------------------
import sys
from math import *

import bpy
from bpy.props import StringProperty
from bpy.types import PropertyGroup

import numpy as np

from AtomBlend.globals import ABGlobals

# append the add-on's path to Blender's python PATH
sys.path.insert(0, ABGlobals.addon_path)


# ------------- Add-on UI -------------
# Class that contains all functions relevant for the UI

# Preferences panel for this Addon in the Blender preferences
class AtomBlendAddonSettings(bpy.types.PropertyGroup):
    # update functions
    def color_update(self, context):
        # reset color list
        ABGlobals.atom_color_list = []

        print(ABGlobals.all_elements_by_name)
        print(bpy.context.scene.color_settings)
        for elem_name in ABGlobals.all_elements_by_name:
            elem_amount = ABGlobals.all_elements_by_name[elem_name]['num_of_atoms']
            print(elem_name, elem_amount)

            col_struct = bpy.context.scene.color_settings[elem_name].color
            col = (col_struct[0], col_struct[1], col_struct[2], col_struct[3])
            ABGlobals.atom_color_list.append([col] * elem_amount)

        # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if isinstance(ABGlobals.atom_color_list[0], list):
            print('CU PRE', ABGlobals.atom_color_list)
            ABGlobals.atom_color_list = [x for xs in ABGlobals.atom_color_list for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists
            print('CU POST', ABGlobals.atom_color_list)


    def alpha_update(self, context):
        # reset color list
        ABGlobals.atom_color_list = []

        for elem_name in ABGlobals.all_elements_by_name:
            elem_amount = ABGlobals.all_elements_by_name[elem_name]['num_of_atoms']
            print(elem_name, elem_amount)

            col_struct = bpy.context.scene.color_settings[elem_name].color
            if bpy.context.scene.color_settings[elem_name].display:
                col = (col_struct[0], col_struct[1], col_struct[2], col_struct[3])
            else:
                col = (col_struct[0], col_struct[1], col_struct[2], 0.0)
            ABGlobals.atom_color_list.append([col] * elem_amount)

        # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if isinstance(ABGlobals.atom_color_list[0], list):
            print('AU PRE', ABGlobals.atom_color_list)
            ABGlobals.atom_color_list = [x for xs in ABGlobals.atom_color_list for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists
            print('AU POST', ABGlobals.atom_color_list)


    def update_point_size(self, context):
        ABGlobals.point_size = context.scene.atom_blend_addon_settings.point_size
        print('')


    # properties
    vertex_percentage: bpy.props.FloatProperty(
        name="Atoms shown",
        default=0.01,
        min=0.0001,
        max=100,
        soft_min=1,
        step=10,
        description="Percentage of atoms shown",
        subtype='PERCENTAGE',
        precision=3
    )

    point_size: bpy.props.FloatProperty(
        name='Point size',
        default=5.0,
        min=0.0,
        max=100.0,
        description='Point size of the atoms',
        update=update_point_size
    )

    # material_settings: bpy.props.FloatVectorProperty(
    #     name="Material",
    #     min=0.0,
    #     max=1.0,
    #     subtype="COLOR",
    #     size=4,
    #     # update=AtomBlendAddonUI.update_background,
    # )

    # for debug purposes
    debug_automatic_file_loading: bpy.props.BoolProperty(
        name='Automatic file loading',
        default=True,
    )


    debug_dataset_selection: bpy.props.EnumProperty(
        name='Dataset Selection',
        items=[('T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01', 'Eisenkorngrenze', 'Eisenkorngrenze'),
               ('T:\Heller\AtomBlendII\Data for iso-surface\R56_02476-v03', 'IsoSurface', 'IsoSurface')
        ],
        default='T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01',
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
        load_file_row.operator('atom_blend_viewer.load_rrng_file', text="Load .rrng file", icon="FILE_FOLDER")

        loaded_row = col.row()
        if ABGlobals.FileLoaded_rrng:
            split_path = ABGlobals.path_rrng.split('\\')
            loaded_row.label(text='Loaded file: ' + split_path[-1])
        else:
            loaded_row.label(text='No file loaded yet...')

        col.row(align=True)

class ATOMBLEND_PT_panel_file(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_panel_file"  # unique identifier for buttons and menu items to reference.
    bl_label = "Load .pos/.epos file"  # display name in the interface.
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
        load_file_row.operator('atom_blend_viewer.load_file', text="Load .pos/.epos file", icon="FILE_FOLDER")

        loaded_row = col.row()
        atoms_shown = col.row()
        if ABGlobals.FileLoaded_e_pos:
            split_path = ABGlobals.path.split('\\')
            loaded_row.label(text='Loaded file: ' + split_path[-1])

            atom_amount = len(ABGlobals.all_data)
            atom_amount = "{:,}".format(atom_amount)  # add comma after every thousand place

            atoms_shown.label(text='Displayed: ' + atom_amount + ' atoms')
        else:
            loaded_row.label(text='No file loaded yet...')
            atoms_shown.label(text='Displayed: n/a')

        col.row(align=True)

class MaterialSetting(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Test Property", default="Unknown")
    color: bpy.props.FloatVectorProperty(name="", subtype='COLOR', min=0.0, max=1.0, size=4, default=(1.0, 0.0, 0.0, 1.0), update=AtomBlendAddonSettings.color_update)
    display: bpy.props.BoolProperty(name="", default=True, update=AtomBlendAddonSettings.alpha_update)

    # list = bpy.props.CollectionProperty(type=MaterialSetting)
    print('mat settings')
    # print('list: ', list)
    # def fill_to(self):
    # list.add()
    print('fill to')

# def test(self, context):
#     cube1_item = bpy.context.scene.my_settings.add()
#     cube1_item.name = 'Cube1'
#     cube1_item.value = 100
#
#     cube2_item = bpy.context.scene.my_settings.add()
#     cube2_item.name = 'Cube2'
#     cube2_item.value = 5



class ATOMBLEND_PT_shader_color_settings(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_shader_color_settings"  # unique identifier for buttons and menu items to reference.
    bl_label = "Color settings"  # display name in the interface.
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    bl_parent_id = "ATOMBLEND_PT_panel_general"

    @classmethod
    def poll(cls, context):
        return True  # context.object is not None

    def draw(self, context):
        layout = self.layout

        if ABGlobals.FileLoaded_rrng or ABGlobals.FileLoaded_e_pos:
            # point size settings
            row = layout.row()
            point_size_col = row.column(align=True)
            point_size_col.prop(context.scene.atom_blend_addon_settings, 'point_size')

            # color settings
            row = layout.row()
            display_col = row.column(align=True)
            name_col = row.column(align=True)
            charge_col = row.column(align=True)
            color_col = row.column(align=True)
            amount_col = row.column(align=True)

            # label row
            display_col.label(text='Display')
            name_col.label(text='Name')
            charge_col.label(text='Charge')
            color_col.label(text='Color')
            amount_col.label(text='Amount')

            for prop in bpy.context.scene.color_settings:
                elem_name_charge = prop.name
                elem_name = elem_name_charge.split('_')[0]
                elem_charge = elem_name_charge.split('_')[1]
                if prop.display:
                    display_col.prop(prop, 'display', icon='HIDE_OFF')
                else:
                    display_col.prop(prop, 'display', icon='HIDE_ON')
                name_col.label(text=elem_name)
                charge_col.label(text=elem_charge)
                color_col.prop(prop, 'color')
                atom_amount = "{:,}".format(ABGlobals.all_elements_by_name[prop.name]['num_of_atoms'])  # add comma after every thousand place
                amount_col.label(text=str(atom_amount))
        else:
            col = layout.column(align=True)
            text_row = col.row()
            text_row.label(text='Load .epos/.pos and .rrng file')




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

    def draw(self, context):
        layout = self.layout
        # only draw if both files are loaded
        # ll = bpy.props.CollectionProperty(type=MaterialSetting)
        # ll.add()
        # box = layout.box()
        # element_row = box.row()

        if ABGlobals.FileLoaded_rrng and ABGlobals.FileLoaded_e_pos:

            # make one top row for labeling
            col = layout.column(align=True)
            row = col.row(align=True)
            # row = col.row(align=True)
            name_col = row.column(align=True)
            charge_col = row.column(align=True)
            color_col = row.column(align=True)

            name_col.label(text='Element')
            charge_col.label(text='Charge')
            color_col.label(text='Color')

            col.separator()

            for obj in bpy.data.objects:
                obj_mats = [m.material for m in obj.material_slots]
                for mat in obj_mats:

                    # add unknown element at the end because elements are stored alphabetically
                    if mat.name == 'unknown_element':
                        continue

                    if mat and mat.use_nodes:
                        bsdf = mat.node_tree.nodes.get("Principled BSDF")
                        row = col.row(align=True)
                        name_col = row.column(align=True)
                        charge_col = row.column(align=True)
                        color_col = row.column(align=True)

                        splitted_name = mat.name.split('_')

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
                charge_col.label(text='n/a')
                color_col.prop(bsdf.inputs['Base Color'], "default_value", text='')

        else:
            col = layout.column(align=True)
            text_row = col.row()
            # text_row.label(text='Load .epos/.pos and .rrng file')
            text_row.label(text='Load .epos/.pos and .rrng file')


class ATOMBLEND_PT_panel_debug(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_panel_debug"  # unique identifier for buttons and menu items to reference.
    bl_label = "DEBUG"  # display name in the interface.
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    bl_parent_id = "ATOMBLEND_PT_panel_general"

    @classmethod
    def poll(cls, context):
        return True  # context.object is not None

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.prop(context.scene.atom_blend_addon_settings, 'debug_dataset_selection')
        col.prop(context.scene.atom_blend_addon_settings, 'debug_automatic_file_loading')
        print(context.scene.atom_blend_addon_settings.debug_dataset_selection)




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
        ABGlobals.path = self.filepath
        # ABGlobals.setup_scene()

        # if there's already an object loaded we want to delete it so we can load another object
        if ABGlobals.FileLoaded_e_pos:
            obj_to_delete = bpy.data.objects['Empty']
            bpy.data.objects.remove(obj_to_delete, do_unlink=True)

        if ABGlobals.path.lower().endswith('.epos'):
            AtomBlendAddon.load_epos_file(self, context)
        elif ABGlobals.path.lower().endswith('.pos'):
            AtomBlendAddon.load_pos_file(self, context)

        ABGlobals.FileLoaded_e_pos = True
        print(f"Object Loaded: {ABGlobals.FileLoaded_e_pos}")

        # print(bpy.data.screens["Modeling-nonnormal"].shading.type)

        # bpy.data.screens["Modeling-nonnormal"].shading.type = "RENDERED"

        # bpy.ops.view3d.toggle_shading(type='RENDERED')

        # https://docs.blender.org/api/current/bpy.types.Operator.html#calling-a-file-selector
        return {'FINISHED'}

    def invoke(self, context, event):
        print(self)
        if context.scene.atom_blend_addon_settings.debug_automatic_file_loading:
            self.filepath = context.scene.atom_blend_addon_settings.debug_dataset_selection + '.epos'
            return self.execute(context)
        else:
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
        ABGlobals.path_rrng = self.filepath
        # ABGlobals.setup_scene()

        if ABGlobals.path_rrng.lower().endswith('.rrng'):
            AtomBlendAddon.load_rrng_file(self, context)

        ABGlobals.FileLoaded_rrng = True
        print(f"Object Loaded: {ABGlobals.FileLoaded_rrng}")

        # https://docs.blender.org/api/current/bpy.types.Operator.html#calling-a-file-selector
        return {'FINISHED'}

    def invoke(self, context, event):
        if context.scene.atom_blend_addon_settings.debug_automatic_file_loading:
            self.filepath = context.scene.atom_blend_addon_settings.debug_dataset_selection + '.rrng'
            return self.execute(context)
        else:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

