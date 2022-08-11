import bpy

from .read_data import *
from .render import *

# ------------------- EXTERNAL MODULES -------------------
import sys
from math import *

import bpy
from bpy.props import StringProperty
from bpy.types import PropertyGroup

import numpy as np

from .globals import ABGlobals

# append the add-on's path to Blender's python PATH
sys.path.insert(0, ABGlobals.addon_path)

# properties for each element
class DisplaySettings(bpy.types.PropertyGroup):
    def total_atom_coords_update(self, context):
        total_atoms_perc_displayed = context.scene.atom_blend_addon_settings.vertex_percentage
        total_atoms_perc_displayed = total_atoms_perc_displayed / len(ABGlobals.all_data)
        print(total_atoms_perc_displayed, len(ABGlobals.all_data), context.scene.atom_blend_addon_settings.vertex_percentage)

        # update function atom_coords_update gets called as we're editing perc_displayed
        for elem_name in ABGlobals.all_elements_by_name:
            bpy.context.scene.color_settings[elem_name].perc_displayed = total_atoms_perc_displayed

        # update other lists
        DisplaySettings.atom_color_update(self, context)
        DisplaySettings.update_point_size(self, context)

    def atom_coords_update(self, context):
        # reset coords list
        ABGlobals.atom_coords = []
        for elem_name in ABGlobals.all_elements_by_name:
            elem_amount = ABGlobals.all_elements_by_name[elem_name]['num_of_atoms']
            perc_displayed = bpy.context.scene.color_settings[elem_name].perc_displayed

            if not bpy.context.scene.color_settings[elem_name].display:
                perc_displayed = 0.0

            if not bpy.context.scene.atom_blend_addon_settings.display_all_atoms:
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
        if len(ABGlobals.atom_coords) > 0 and isinstance(ABGlobals.atom_coords[0], list):
            ABGlobals.atom_coords = [x for xs in ABGlobals.atom_coords for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

        # update other lists
        DisplaySettings.atom_color_update(self, context)
        DisplaySettings.update_point_size(self, context)

    def atom_color_update(self, context):
        # reset color list
        ABGlobals.atom_color_list = []

        for elem_name in ABGlobals.all_elements_by_name:
            num_displayed = ABGlobals.all_elements_by_name[elem_name]['num_displayed']

            col_struct = bpy.context.scene.color_settings[elem_name].color
            col = (col_struct[0], col_struct[1], col_struct[2], col_struct[3])
            ABGlobals.atom_color_list.append([col] * num_displayed)

        # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if len(ABGlobals.atom_color_list) > 0 and isinstance(ABGlobals.atom_color_list[0], list):
            ABGlobals.atom_color_list = [x for xs in ABGlobals.atom_color_list for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

    def update_point_size(self, context):
        ABGlobals.point_size_list = []
        print('UPDATE POINT SIZE DISPLAY SETTINGS')

        for elem_name in ABGlobals.all_elements_by_name:
            num_displayed = ABGlobals.all_elements_by_name[elem_name]['num_displayed']
            point_size = bpy.context.scene.color_settings[elem_name].point_size
            ABGlobals.point_size_list.append([point_size] * num_displayed)
            print(elem_name, point_size, num_displayed, len(ABGlobals.point_size_list))

        # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if len(ABGlobals.point_size_list) > 0 and isinstance(ABGlobals.point_size_list[0], list):
            ABGlobals.point_size_list = [x for xs in ABGlobals.point_size_list for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

    name: bpy.props.StringProperty(name="Test Property", default="Unknown")
    color: bpy.props.FloatVectorProperty(name="", subtype='COLOR', min=0.0, max=1.0, size=4, default=(0.4, 0.4, 0.4, 1.0), update=atom_color_update)
    display: bpy.props.BoolProperty(name="", default=True, update=atom_coords_update)
    perc_displayed: bpy.props.FloatProperty(name="", default=1.0, min=0.0, soft_min=0.0, soft_max=1.0, step=0.01, precision=4, update=atom_coords_update)
    point_size: bpy.props.FloatProperty(name="", default=5.0, min=0.0, soft_min=0.0, step=0.5, precision=2, update=update_point_size)


# Properties for all elements
class AB_properties(bpy.types.PropertyGroup):
    # update functions
    def update_point_size(self, context):
        print('UPDATE POINT SIZE AB PROP')
        general_point_size = context.scene.atom_blend_addon_settings.point_size

        for elem_name in ABGlobals.all_elements_by_name:
            bpy.context.scene.color_settings[elem_name].point_size = general_point_size

    def update_camera_location_x(self, context):
        new_loc_x = context.scene.atom_blend_addon_settings.camera_location_x
        bpy.context.scene.camera.location[0] = new_loc_x

    def update_camera_location_y(self, context):
        new_loc_y = context.scene.atom_blend_addon_settings.camera_location_y
        bpy.context.scene.camera.location[1] = new_loc_y

    def update_camera_location_z(self, context):
        new_loc_z = context.scene.atom_blend_addon_settings.camera_location_z
        bpy.context.scene.camera.location[2] = new_loc_z

    def update_background_color(self, context):
        bc = context.scene.atom_blend_addon_settings.background_color
        bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (bc[0], bc[1], bc[2], 1.0)

    # properties
    e_pos_filepath: bpy.props.StringProperty(name='', default='', description='')
    rrng_filepath: bpy.props.StringProperty(name='', default='', description='')
    vertex_percentage: bpy.props.FloatProperty(name="Total displayed", default=0.001, min=0.000001, max=1.0, soft_min=1, step=0.01, description="Percentage of displayed atoms", precision=4, update=DisplaySettings.total_atom_coords_update)
    point_size: bpy.props.FloatProperty(name='Point size', default=5.0, min=0.0, max=100.0, step=0.5, description='Point size of the atoms', update=update_point_size)
    display_all_atoms: bpy.props.BoolProperty(name='', default=True, description='Display or hide all elements', update=DisplaySettings.atom_coords_update)
    background_color: bpy.props.FloatVectorProperty(name='Background color', subtype='COLOR', description='Background color for rendering', min=0.0, max=1.0, default=[1.0, 1.0, 1.0], update=update_background_color)
    camera_location_x: bpy.props.FloatProperty(name='X', description='Changes the x coordinate of the camera location', update=update_camera_location_x)
    camera_location_y: bpy.props.FloatProperty(name='Y', description='Changes the y coordinate of the camera location', update=update_camera_location_y)
    camera_location_z: bpy.props.FloatProperty(name='Z', description='Changes the z coordinate of the camera location', update=update_camera_location_z)

    # for developing purposes
    dev_automatic_file_loading: bpy.props.BoolProperty(name='Automatic file loading', default=True)
    dev_dataset_selection: bpy.props.EnumProperty(
        name='Dataset Selection',
        items=[('T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01', 'Eisenkorngrenze', 'Eisenkorngrenze'),
               ('T:\Heller\AtomBlendII\Data for iso-surface\R56_02476-v03', 'IsoSurface', 'IsoSurface')
        ],
        default='T:\Heller\AtomBlendII\EisenKorngrenze\R56_03446-v01',
    )
    dev_quick_file_loading: bpy.props.BoolProperty(name='Quick file loading', default=False)

class ATOMBLEND_PT_panel_general(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_panel_general"  # unique identifier for buttons and menu items to reference.
    bl_label = "AtomBlend-II"  # display name in the interface.
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"

    def draw(self, context):
        layout = self.layout


class ATOMBLEND_PT_panel_file(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_panel_file"  # unique identifier for buttons and menu items to reference.
    bl_label = "File loading"  # display name in the interface.
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

        # .pos/.epos file
        load_e_pos_file_row = layout.row(align=True)
        col = load_e_pos_file_row.split(factor=0.3)
        col.label(text='.pos/.epos file:')
        col = col.split(factor=1.0)
        col.prop(bpy.context.scene.atom_blend_addon_settings, 'e_pos_filepath')
        col.enabled = False
        col = load_e_pos_file_row.column(align=True)
        col.operator('atom_blend_viewer.load_file', icon='FILE_FOLDER')

        # .rrng file
        load_rrng_file_row = layout.row(align=True)
        col = load_rrng_file_row.split(factor=0.3)
        col.label(text='.rrng file:')
        col = col.split(factor=1.0)
        col.prop(bpy.context.scene.atom_blend_addon_settings, 'rrng_filepath')
        col.enabled = False
        col = load_rrng_file_row.column(align=True)
        col.operator('atom_blend_viewer.load_rrng_file', icon="FILE_FOLDER")


class ATOMBLEND_PT_shader_display_settings(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_shader_display_settings"  # unique identifier for buttons and menu items to reference.
    bl_label = "Display settings"  # display name in the interface.
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
            # col = layout.column()
            # display_col = row.column()
            split = layout.split(factor=0.1)
            display_col = split.column()
            split = split.split(factor=0.05 / 0.9)
            name_col = split.column()
            split = split.split(factor=0.05 / 0.85)
            charge_col = split.column()
            split = split.split(factor=0.1 / 0.8)
            color_col = split.column()
            split = split.split(factor=0.2 / 0.6)
            point_size_col = split.column()
            split = split.split(factor=0.2 / 0.4)
            displayed_col = split.column()
            split = split.split(factor=0.2 / 0.2)
            amount_col = split.column()
            split = split.split(factor=0.0)

            # label row
            # prop = context.scene.atom_blend_addon_settings
            # display_col.prop(prop, 'display_all_atoms', icon_only=True, icon='HIDE_OFF' if prop.display_all_atoms else 'HIDE_ON')
            display_col.label(text='')
            name_col.label(text='Name')
            charge_col.label(text='Charge')
            color_col.label(text='Color')
            point_size_col.label(text='Point size')
            displayed_col.label(text='% Displayed')
            amount_col.label(text='# Displayed')

            for prop in bpy.context.scene.color_settings:
                if prop.name == ABGlobals.unknown_label:  # add unknown atoms in the last row
                    continue

                elem_name_charge = prop.name
                elem_name = elem_name_charge.split('_')[0]
                elem_charge = elem_name_charge.split('_')[1]
                display_col.prop(prop, 'display', icon_only=True, icon='HIDE_OFF' if prop.display else 'HIDE_ON')
                name_col.label(text=elem_name)
                charge_col.label(text=elem_charge)
                color_col.prop(prop, 'color')
                point_size_col.prop(prop, 'point_size')
                displayed_col.prop(prop, 'perc_displayed')
                atom_amount_shown = "{:,}".format(ABGlobals.all_elements_by_name[prop.name]['num_displayed'])  # add comma after every thousand place
                atom_amount_available = "{:,}".format(ABGlobals.all_elements_by_name[prop.name]['num_of_atoms'])  # add comma after every thousand place
                amount_col.label(text=str(atom_amount_shown) + '/' + str(atom_amount_available))

            # display unknown atoms in last row
            prop = bpy.context.scene.color_settings[ABGlobals.unknown_label]
            elem_name_charge = prop.name
            elem_name = elem_name_charge.split('_')[0]
            elem_charge = elem_name_charge.split('_')[1]
            display_col.prop(prop, 'display', icon_only=True, icon='HIDE_OFF' if prop.display else 'HIDE_ON')
            name_col.label(text=elem_name)
            charge_col.label(text=elem_charge)
            color_col.prop(prop, 'color')
            point_size_col.prop(prop, 'point_size')
            displayed_col.prop(prop, 'perc_displayed')
            atom_amount_shown = "{:,}".format(ABGlobals.all_elements_by_name[prop.name]['num_displayed'])  # add comma after every thousand place
            atom_amount_available = "{:,}".format(ABGlobals.all_elements_by_name[prop.name]['num_of_atoms'])  # add comma after every thousand place
            amount_col.label(text=str(atom_amount_shown) + '/' + str(atom_amount_available))


class ATOMBLEND_PT_panel_dev(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_panel_dev"  # unique identifier for buttons and menu items to reference.
    bl_label = "Development Extras"  # display name in the interface.
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    bl_parent_id = "ATOMBLEND_PT_panel_general"
    bl_options = {'DEFAULT_CLOSED'}

    # @classmethod
    # def poll(cls, context):
    #     return True  # context.object is not None

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.prop(bpy.context.scene.atom_blend_addon_settings, 'dev_dataset_selection')
        col.prop(bpy.context.scene.atom_blend_addon_settings, 'dev_automatic_file_loading')

        # quick file loading
        # row = col.row()
        # row.prop(bpy.context.scene.atom_blend_addon_settings, 'dev_quick_file_loading')
        # row.prop(bpy.context.scene.atom_blend_addon_settings, 'vertex_percentage')

class ATOMBLEND_PT_rendering(bpy.types.Panel):
    bl_idname = "ATOMBLEND_PT_rendering"
    bl_label = "Render picture"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AtomBlend-II"
    bl_parent_id = "ATOMBLEND_PT_panel_general"

    @classmethod
    def poll(cls, context):
        # the panel should always be drawn
        return True

    def draw(self, context):
        layout = self.layout

        if ABGlobals.FileLoaded_e_pos:
            # camera settings
            col = layout.column(align=True)
            col.label(text='Camera location:')
            col.prop(context.scene.atom_blend_addon_settings, 'camera_location_x')
            col.prop(context.scene.atom_blend_addon_settings, 'camera_location_y')
            col.prop(context.scene.atom_blend_addon_settings, 'camera_location_z')

            # background color
            background_color = layout.row(align=True)
            background_color.prop(context.scene.atom_blend_addon_settings, 'background_color')

            # render
            row = layout.row()
            preview_col = row.column(align=True)
            render_col = row.column(align=True)
            preview_col.operator('atom_blend.preview', icon='SEQ_PREVIEW')
            render_col.operator('atom_blend.rendering', icon='RENDER_STILL')

            if context.space_data.region_3d.view_perspective == 'PERSP':
                pass
            elif context.space_data.region_3d.view_perspective == 'CAMERA':
                pass

            # if not ABGlobals.FileLoaded_e_pos:
            #     row.enabled = False
            # else:
            #     row.enabled = True


# Operators used for buttons
class ATOMBLEND_OT_load_file(bpy.types.Operator):
    bl_idname = "atom_blend_viewer.load_file"
    bl_label = ""
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
            obj_to_delete = bpy.data.objects['Center']
            bpy.data.objects.remove(obj_to_delete, do_unlink=True)

        if ABGlobals.path.lower().endswith('.epos'):
            AtomBlendAddon.load_epos_file(self, context)
        elif ABGlobals.path.lower().endswith('.pos'):
            AtomBlendAddon.load_pos_file(self, context)

        ABGlobals.FileLoaded_e_pos = True
        print(f"Object Loaded: {ABGlobals.FileLoaded_e_pos}")

        # set filepath to property
        bpy.context.scene.atom_blend_addon_settings.e_pos_filepath = self.filepath

        return {'FINISHED'}

    def invoke(self, context, event):
        if context.scene.atom_blend_addon_settings.dev_automatic_file_loading:
            self.filepath = context.scene.atom_blend_addon_settings.dev_dataset_selection + '.epos'
            return self.execute(context)
        else:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

class ATOMBLEND_OT_load_rrng_file(bpy.types.Operator):
    bl_idname = "atom_blend_viewer.load_rrng_file"
    bl_label = ""
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

        # set filepath to property
        bpy.context.scene.atom_blend_addon_settings.rrng_filepath = self.filepath

        # https://docs.blender.org/api/current/bpy.types.Operator.html#calling-a-file-selector
        return {'FINISHED'}

    def invoke(self, context, event):
        if context.scene.atom_blend_addon_settings.dev_automatic_file_loading:
            self.filepath = context.scene.atom_blend_addon_settings.dev_dataset_selection + '.rrng'
            return self.execute(context)
        else:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

class ATOMBLEND_OT_rendering(bpy.types.Operator):
    bl_idname = "atom_blend.rendering"
    bl_label = "Rendering"
    bl_description = "Render one frame of the scene"

    @classmethod
    def poll(cls, context):
        return True  # context.object is not None

    def execute(self, context):
        ABManagement.save_image(self, context)
        return {'FINISHED'}

class ATOMBLEND_OT_preview(bpy.types.Operator):
    bl_idname = "atom_blend.preview"
    bl_label = "Render preview"
    bl_description = "Preview the render"

    @classmethod
    def poll(cls, context):
        return True  # context.object is not None

    def execute(self, context):
        # toggle (normal) perspective view and camera view
        # for area in bpy.context.screen.areas:
            # if area.type == 'VIEW_3D':
        if context.space_data.region_3d.view_perspective == 'PERSP':
            context.space_data.region_3d.view_perspective = 'CAMERA'
        elif context.space_data.region_3d.view_perspective == 'CAMERA':
            context.space_data.region_3d.view_perspective = 'PERSP'

        return {'FINISHED'}