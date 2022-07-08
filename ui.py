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

    '''
    def num_displayed(self, context):
        # reset color list
        ABGlobals.atom_color_list = []

        for elem_name in ABGlobals.all_elements_by_name:
            num_displayed = ABGlobals.all_elements_by_name[elem_name]['num_displayed']

            col_struct = bpy.context.scene.color_settings[elem_name].color

            # if atoms are not displayed, they stay invisible if color is changed
            if bpy.context.scene.color_settings[elem_name].display:
                col = (col_struct[0], col_struct[1], col_struct[2], col_struct[3])
            else:
                col = (col_struct[0], col_struct[1], col_struct[2], 0.0)

    def atom_display_update(self, context):
        # reset color list
        ABGlobals.atom_color_list = []

        for elem_name in ABGlobals.all_elements_by_name:
            elem_amount = ABGlobals.all_elements_by_name[elem_name]['num_of_atoms']

            col_struct = bpy.context.scene.color_settings[elem_name].color

            # if atoms are not displayed, they stay invisible if color is changed
            if bpy.context.scene.color_settings[elem_name].display:
                col = (col_struct[0], col_struct[1], col_struct[2], col_struct[3])
            else:
                col = (col_struct[0], col_struct[1], col_struct[2], 0.0)
            ABGlobals.atom_color_list.append([col] * elem_amount)

        # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if isinstance(ABGlobals.atom_color_list[0], list):
            ABGlobals.atom_color_list = [x for xs in ABGlobals.atom_color_list for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists
    '''

    def total_atom_coords_update(self, context):
        print('TOTAL ATOM COORDS UPDATE')
        '''
        ABGlobals.atom_coords = []
        for elem_name in ABGlobals.all_elements_by_name:
            elem_amount = ABGlobals.all_elements_by_name[elem_name]['num_of_atoms']
            total_atoms_perc_displayed = context.scene.atom_blend_addon_settings.vertex_percentage

            if not bpy.context.scene.color_settings[elem_name].display:
                total_atoms_perc_displayed = 0.0

            num_displayed = int(elem_amount * total_atoms_perc_displayed)
            ABGlobals.all_elements_by_name[elem_name]['num_displayed'] = num_displayed

            print(elem_name, num_displayed, elem_amount, total_atoms_perc_displayed)

            # build coord list for shader according to the new shown percentage
            this_elem_coords = ABGlobals.all_elements_by_name[elem_name]['coordinates'][:num_displayed]
            ABGlobals.atom_coords.append(this_elem_coords)

            bpy.context.scene.color_settings[elem_name].perc_displayed = total_atoms_perc_displayed

        # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if isinstance(ABGlobals.atom_coords[0], list):
            ABGlobals.atom_coords = [x for xs in ABGlobals.atom_coords for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

        # update color list
        AtomBlendAddonSettings.atom_color_update(self, context)
        '''

        total_atoms_perc_displayed = context.scene.atom_blend_addon_settings.vertex_percentage

        # update function atom_coords_update gets called as we're editing perc_displayed
        for elem_name in ABGlobals.all_elements_by_name:
            bpy.context.scene.color_settings[elem_name].perc_displayed = total_atoms_perc_displayed

    def atom_coords_update(self, context):
        print('ATOM COORDS UPDATE')
        # reset coords list
        ABGlobals.atom_coords = []
        for elem_name in ABGlobals.all_elements_by_name:
            elem_amount = ABGlobals.all_elements_by_name[elem_name]['num_of_atoms']
            perc_displayed = bpy.context.scene.color_settings[elem_name].perc_displayed

            if not bpy.context.scene.color_settings[elem_name].display:
                perc_displayed = 0.0

            # if perc_displayed > 1.0 the input is not a percentage but an amount -> we calculate the percentage
            if perc_displayed > 1.0:
                num_displayed = int(perc_displayed)
                if num_displayed > elem_amount:
                    num_displayed = elem_amount
                perc_displayed = num_displayed / elem_amount
                bpy.context.scene.color_settings[elem_name].perc_displayed = perc_displayed
                return
            else:
                num_displayed = int(math.ceil(elem_amount * perc_displayed))

            ABGlobals.all_elements_by_name[elem_name]['num_displayed'] = num_displayed

            # build coord list for shader according to the new shown percentage
            this_elem_coords = ABGlobals.all_elements_by_name[elem_name]['coordinates'][:num_displayed]
            ABGlobals.atom_coords.append(this_elem_coords)

        # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if isinstance(ABGlobals.atom_coords[0], list):
            ABGlobals.atom_coords = [x for xs in ABGlobals.atom_coords for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

        # update color list
        AtomBlendAddonSettings.atom_color_update(self, context)

    def atom_color_update(self, context):
        print('ATOM COLOR UPDATE')
        # reset color list
        ABGlobals.atom_color_list = []

        for elem_name in ABGlobals.all_elements_by_name:
            num_displayed = ABGlobals.all_elements_by_name[elem_name]['num_displayed']

            col_struct = bpy.context.scene.color_settings[elem_name].color
            col = (col_struct[0], col_struct[1], col_struct[2], col_struct[3])
            ABGlobals.atom_color_list.append([col] * num_displayed)
            print(elem_name, num_displayed)

        # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if isinstance(ABGlobals.atom_color_list[0], list):
            ABGlobals.atom_color_list = [x for xs in ABGlobals.atom_color_list for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

    def update_point_size(self, context):
        ABGlobals.point_size = context.scene.atom_blend_addon_settings.point_size

    # properties
    vertex_percentage: bpy.props.FloatProperty(
        name="Atoms shown",
        default=0.001,
        min=0.000001,
        max=1.0,
        soft_min=1,
        step=10,
        description="Percentage of atoms shown",
        precision=4,
        update=total_atom_coords_update
    )

    point_size: bpy.props.FloatProperty(
        name='Point size',
        default=5.0,
        min=0.0,
        max=100.0,
        description='Point size of the atoms',
        update=update_point_size
    )

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

class MaterialSetting(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Test Property", default="Unknown")
    color: bpy.props.FloatVectorProperty(name="", subtype='COLOR', min=0.0, max=1.0, size=4, default=(1.0, 0.0, 0.0, 1.0), update=AtomBlendAddonSettings.atom_color_update)
    display: bpy.props.BoolProperty(name="", default=True, update=AtomBlendAddonSettings.atom_coords_update)
    perc_displayed: bpy.props.FloatProperty(name="", default=1.0, min=0.0, soft_min=0.0, soft_max=1.0, step=0.01, precision=4, update=AtomBlendAddonSettings.atom_coords_update)


class ATOMBLEND_PT_panel_general(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_panel_general"  # unique identifier for buttons and menu items to reference.
    bl_label = "AtomBlend-II"  # display name in the interface.
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"

    def draw(self, context):
        layout = self.layout

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

        load_file_row = col.row()
        load_file_row.operator('atom_blend_viewer.load_file', text="Load .pos/.epos file", icon="FILE_FOLDER")

        loaded_row = col.row()
        # atoms_shown = col.row()
        if ABGlobals.FileLoaded_e_pos:
            # if not ABGlobals.FileLoaded_rrng:
            #     vertex_percentage_row = col.row()
            #     vertex_percentage_row.prop(context.scene.atom_blend_addon_settings, "vertex_percentage")

            split_path = ABGlobals.path.split('\\')
            loaded_row.label(text='Loaded file: ' + split_path[-1])

            # atom_amount = len(ABGlobals.all_data)
            # atom_amount = "{:,}".format(atom_amount)  # add comma after every thousand place
            #
            # atoms_shown.label(text='Displayed: ' + atom_amount + ' atoms')
        else:
            loaded_row.label(text='No file loaded yet...')
            # atoms_shown.label(text='Displayed: n/a')

        col.row(align=True)


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

            # total atoms shown in percentage
            vertex_percentage_row = layout.row()
            vertex_percentage_col = vertex_percentage_row.column(align=True)
            vertex_percentage_col.prop(context.scene.atom_blend_addon_settings, "vertex_percentage")

            # color settings
            row = layout.row()
            display_col = row.column(align=True)
            name_col = row.column(align=True)
            charge_col = row.column(align=True)
            color_col = row.column(align=True)
            displayed_col = row.column(align=True)
            amount_col = row.column(align=True)

            # label row
            display_col.label(text='')
            name_col.label(text='Name')
            charge_col.label(text='Charge')
            color_col.label(text='Color')
            displayed_col.label(text='Displayed')
            amount_col.label(text='Shown')

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
                displayed_col.prop(prop, 'perc_displayed')
                atom_amount_shown = "{:,}".format(ABGlobals.all_elements_by_name[prop.name]['num_displayed'])  # add comma after every thousand place
                atom_amount_available = "{:,}".format(ABGlobals.all_elements_by_name[prop.name]['num_of_atoms'])  # add comma after every thousand place
                amount_col.label(text=str(atom_amount_shown) + '/' + str(atom_amount_available))
        else:
            col = layout.column(align=True)
            text_row = col.row()
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

        return {'FINISHED'}

    def invoke(self, context, event):
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

