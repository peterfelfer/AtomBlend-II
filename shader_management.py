import math

import bpy
import gpu
import blf
from blf import ROTATION
from gpu.types import GPUShader

from .shaders import *
# from .read_data import AtomBlendAddon
from .read_data import *
from gpu_extras.batch import batch_for_shader
from .globals import ABGlobals
import numpy as np
import bpy_extras
import bpy_extras.view3d_utils
import mathutils
import bpy_extras.object_utils as object_utils


class ABManagement:
    cache = {}

    def get_3d_to_2d_viewport(self, point_3d):
        point_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, point_3d)
        return point_2d

    def init(self, context):
        # --- init shader ---
        shader = GPUShader(ABShaders.vertex_shader_simple, ABShaders.fragment_shader_simple)
        # line_shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        # line_shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        my_line_shader = GPUShader(ABShaders.metric_vertex_shader, ABShaders.metric_fragment_shader)
        legend_shader = GPUShader(ABShaders.legend_vertex_shader, ABShaders.legend_fragment_shader)

        # shader input
        ABGlobals.atom_color_list = []

        # init point sizes
        ABGlobals.point_size_list = []

        for elem_name in ABGlobals.all_elements_by_name:
            num_displayed = ABGlobals.all_elements_by_name[elem_name]['num_displayed']
            point_size = bpy.context.scene.color_settings[elem_name].point_size
            ABGlobals.point_size_list.append([point_size] * num_displayed)

        # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if len(ABGlobals.point_size_list) > 0 and isinstance(ABGlobals.point_size_list[0], list):
            ABGlobals.point_size_list = [x for xs in ABGlobals.point_size_list for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

        bpy.context.scene.color_settings[elem_name].perc_displayed = bpy.context.scene.atom_blend_addon_settings.vertex_percentage

        # add draw handler that will be called every time this region in this space type will be drawn
        # ABManagement.handle = bpy.types.SpaceView3D.draw_handler_add(ABManagement.handler, (self, context), 'WINDOW', 'POST_VIEW')
        ABManagement.handle = bpy.types.SpaceView3D.draw_handler_add(ABManagement.handler, (self, context), 'WINDOW', 'POST_PIXEL')

        # --- init other things needed for shader drawing ---
        # create empty to move the atom tip to the center (0,0,0)
        center_x = (ABGlobals.max_x + ABGlobals.min_x) / 2
        center_y = (ABGlobals.max_y + ABGlobals.min_y) / 2
        center_z = (ABGlobals.max_z + ABGlobals.min_z) / 2

        # print(center_x, center_y, center_z)
        if (bpy.context.scene.objects.get('Top') == None):
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, ABGlobals.max_z))
            bpy.data.objects['Empty'].name = 'Top'

        # create empty representing the approximate center of the atom tip
        if (bpy.context.scene.objects.get('Center') == None):
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=(center_x, center_y, center_z))
            bpy.data.objects['Empty'].name = 'Center'

        # create empty representing the origin (0,0,0)
        if (bpy.context.scene.objects.get('Origin') == None):
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
            bpy.data.objects['Empty'].name = 'Origin'

        # create empty representing the origin of the scaling cube
        if (bpy.context.scene.objects.get('Scaling Cube') == None):
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
            bpy.data.objects['Empty'].name = 'Scaling Cube'

        # create empty representing the approximate center of the atom tip
        if (bpy.context.scene.objects.get('Camera Tracker') == None):
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=(center_x, center_y, center_z))
            bpy.data.objects['Empty'].name = 'Camera Tracker'

        # rotate tip 180 degrees around x axis
        bpy.data.objects['Top'].rotation_euler[0] = math.pi

        # set camera if it doesn't exist yet
        if bpy.context.scene.camera is None:
            # calculate camera position
            bpy.ops.object.camera_add(location=(0, 0, 0))
            bpy.data.objects["Camera"].rotation_euler = (-0.5 * math.pi, 0, 0)

        # track camera to camera tracker (atom tip)
        constraint = bpy.data.objects['Camera'].constraints.new('TRACK_TO')
        constraint.target = bpy.data.objects['Camera Tracker']

        bpy.data.cameras["Camera"].clip_end = 5000
        bpy.data.objects['Camera'].location[1] = bpy.data.objects['Center'].location[1] + 300
        bpy.data.objects['Camera'].location[2] = bpy.data.objects['Center'].location[2]

        # set frames of timeline
        bpy.data.scenes["Scene"].frame_end = context.scene.atom_blend_addon_settings.frames
        context.scene.atom_blend_addon_settings.frames = 50

        # save in cache
        cache = ABManagement.cache
        cache['shader'] = shader
        cache['my_line_shader'] = my_line_shader
        cache['camera'] = bpy.context.scene.camera
        cache['legend_shader'] = legend_shader

        # set background color
        bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = [1.0, 1.0, 1.0, 1.0]

        # hide objects in viewport
        bpy.data.objects['Camera'].hide_set(True)
        bpy.data.objects['Center'].hide_set(True)
        bpy.data.objects['Top'].hide_set(True)
        bpy.data.objects['Origin'].hide_set(True)
        bpy.data.objects['Scaling Cube'].hide_set(True)
        bpy.data.objects['Camera Tracker'].hide_set(True)

        # set default path
        bpy.data.scenes["Scene"].render.filepath = bpy.data.scenes["Scene"].render.filepath + ABGlobals.dataset_name + '.png'

        # set defreault positions for camera sliders
        center_x = (ABGlobals.max_x + ABGlobals.min_x) / 2
        center_z = (ABGlobals.max_z + ABGlobals.min_z) / 2
        context.scene.atom_blend_addon_settings.camera_pos_x = center_x
        context.scene.atom_blend_addon_settings.camera_pos_z = center_z

    def handler(self, context):
        if not ABGlobals.FileLoaded_e_pos and not ABGlobals.FileLoaded_rrng:
            return

        # update camera position in addon (if the camera is moved via viewport)
        if bpy.context.scene.camera is not None:
            cam_loc = bpy.data.objects["Camera"].location
            context.scene.atom_blend_addon_settings.camera_location_x_frame = cam_loc[0]
            context.scene.atom_blend_addon_settings.camera_location_y_frame = cam_loc[1]
            context.scene.atom_blend_addon_settings.camera_location_z_frame = cam_loc[2]

        gpu.state.blend_set('ALPHA')
        gpu.state.program_point_size_set(True)
        # gpu.state.depth_mask_set(False)
        # gpu.state.depth_test_set('ALWAYS')
        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.depth_mask_set(True)

        # render frame
        ABManagement.render(self, context)
        if bpy.context.scene.atom_blend_addon_settings.scaling_cube:
            # ABManagement.render_metric(self, context)
            ABManagement.create_bounding_box(self, context)

        ABManagement.create_legend(self, context)

        gpu.state.depth_mask_set(False)

    def create_legend(self, context, render_img=False):
        # functions to set a value/vec2 into relation with the render resolution to map it into the viewport
        def in_relation_vec2(value):
            return mathutils.Vector((value[0] / render_width, value[1] / render_height))

        def in_relation_x(value):
            return value / render_width

        def in_relation_y(value):
            return value / render_height

        if not context.scene.atom_blend_addon_settings.legend:
            return

        cache = ABManagement.cache
        cam_obj = bpy.context.scene.camera
        cam = cam_obj.data

        viewport_width = bpy.context.region.width
        viewport_height = bpy.context.region.height

        render_width = bpy.context.scene.render.resolution_x
        render_height = bpy.context.scene.render.resolution_y

        # upper_right = cam.view_frame(scene=bpy.context.scene)[0]
        lower_right = cam.view_frame(scene=bpy.context.scene)[1]
        lower_left = cam.view_frame(scene=bpy.context.scene)[2]
        upper_left = cam.view_frame(scene=bpy.context.scene)[3]

        # object space -> world space
        lower_left = cam_obj.matrix_world @ lower_left
        lower_right = cam_obj.matrix_world @ lower_right
        upper_left = cam_obj.matrix_world @ upper_left

        # world space -> screen space
        lower_left_viewport = ABManagement.get_3d_to_2d_viewport(self, lower_left)
        lower_right_viewport = ABManagement.get_3d_to_2d_viewport(self, lower_right)
        upper_left_viewport = ABManagement.get_3d_to_2d_viewport(self, upper_left)

        if lower_left_viewport is None:
            return

        viewport_camera_measurement = mathutils.Vector((lower_right_viewport.x - lower_left_viewport.x, upper_left_viewport.y - lower_left_viewport.y))

        legend_point_size = in_relation_x(context.scene.atom_blend_addon_settings.legend_point_size) * viewport_camera_measurement.x
        line_spacing = context.scene.atom_blend_addon_settings.legend_line_spacing

        legend_y_element_space = in_relation_y(line_spacing) * viewport_camera_measurement.y # space between element color point and element name

        # we have to set the placement of the legend on the rendered image in relation to the viewport
        legend_start_pos = mathutils.Vector((context.scene.atom_blend_addon_settings.legend_position_x, context.scene.atom_blend_addon_settings.legend_position_y))

        legend_pos_viewport = lower_left_viewport + in_relation_vec2(legend_start_pos) * viewport_camera_measurement
        # legend_pos_viewport = lower_left_viewport + legend_start_pos # for the viewport the lower left corner of camera can be zoomed in/out with camera wheel
        legend_pos_image = legend_start_pos # for rendered image the lower left corner is just (0,0)
        vertices = []
        colors = []
        point_size = []
        counter = 0

        # go through color_settings in reverse order because legend
        # should be displayed in the same order as in ui (the ui is drawn bottom to top)
        keys = context.scene.color_settings.keys()
        keys.remove(ABGlobals.unknown_label)
        keys.append(ABGlobals.unknown_label)
        keys.reverse() # in place reverse
        # remove the unknown label from its index and add it to the last row
        # print('----')
        for k in keys:
            # print('key', k)
            prop = bpy.context.scene.color_settings[k]
            if not prop.display and context.scene.atom_blend_addon_settings.legend_hide_hidden_elements:
                continue

            elem_name = prop.display_name
            color = prop.color

            if render_img:
                point_size.append(context.scene.atom_blend_addon_settings.legend_point_size)
                if counter != 0:
                    legend_pos_image += mathutils.Vector((0.0, line_spacing))
                screen_space = mathutils.Vector((float(legend_pos_image.x / render_width), float(legend_pos_image.y / render_height)))

            else:
                point_size.append(legend_point_size)
                if counter != 0:
                    legend_pos_viewport += mathutils.Vector((0.0, legend_y_element_space))
                screen_space = mathutils.Vector((float(legend_pos_viewport.x / viewport_width), float(legend_pos_viewport.y / viewport_height)))

            clip_space = screen_space * mathutils.Vector((2.0, 2.0)) - mathutils.Vector((1.0, 1.0)) # [0,1] -> [-1,1] mapping

            vertices.append((clip_space.x, clip_space.y, 0))
            colors.append(color)
            counter += 1

            # draw font
            font_id = 0
            color = context.scene.atom_blend_addon_settings.legend_font_color
            blf.color(font_id, color[0], color[1], color[2], color[3])
            if render_img:
                radius = context.scene.atom_blend_addon_settings.legend_point_size / 2.0
                font_size = context.scene.atom_blend_addon_settings.legend_font_size
                blf.size(font_id, font_size)
                x_dim, y_dim = blf.dimensions(font_id, elem_name)
                column_spacing = context.scene.atom_blend_addon_settings.legend_column_spacing
                blf.position(font_id, legend_pos_image.x + column_spacing + radius, legend_pos_image.y - y_dim / 2.0, 0)
            else:
                radius = legend_point_size / 2.0
                font_size = in_relation_y(context.scene.atom_blend_addon_settings.legend_font_size) * viewport_camera_measurement.y
                blf.size(font_id, font_size)
                x_dim, y_dim = blf.dimensions(font_id, elem_name)
                # blf.position(font_id, legend_pos_viewport.x + 20 + radius, legend_pos_viewport.y - font_dim[1] / 2.0, 0)
                column_spacing = in_relation_x(context.scene.atom_blend_addon_settings.legend_column_spacing) * viewport_camera_measurement.x
                blf.position(font_id, legend_pos_viewport.x + column_spacing + radius, legend_pos_viewport.y - (y_dim / 2.0), 0)

            # blf.position(font_id, 100, 100, 0)
            blf.draw(font_id, elem_name)

        shader = cache['legend_shader']
        batch = batch_for_shader(shader, 'POINTS', {'position': vertices, 'color': colors, 'ps': point_size})
        shader.bind()
        batch.draw(shader)

    def create_bounding_box(self, context, proj_matrix=None, object_matrix=None):
        cache = ABManagement.cache
        line_shader = cache['my_line_shader']

        # multiply min and max by the scale of the scaling box. the range of x and y is app. [-x, x] and [-y, y] while the range of z is app. [0, z], therefore we need another calculation for z.
        scale = context.scene.atom_blend_addon_settings.scaling_cube_scale
        center_z = ABGlobals.max_z / 2.0
        xmin = bpy.data.objects['Scaling Cube'].location[0] + ABGlobals.min_x * scale[0]
        xmax = bpy.data.objects['Scaling Cube'].location[0] + ABGlobals.max_x * scale[0]
        ymin = bpy.data.objects['Scaling Cube'].location[1] + ABGlobals.min_y * scale[1]
        ymax = bpy.data.objects['Scaling Cube'].location[1] + ABGlobals.max_y * scale[1]
        zmin = bpy.data.objects['Scaling Cube'].location[2] - (center_z * scale[2]) + center_z
        zmax = bpy.data.objects['Scaling Cube'].location[2] + (center_z * scale[2]) + center_z
        # zmin = ABGlobals.min_z
        # zmax = ABGlobals.max_z
        # zmin = (ABGlobals.min_z + bpy.data.objects['Center'].location[2]) * scale[2]
        # zmax = (ABGlobals.max_z + bpy.data.objects['Center'].location[2]) * scale[2]

        bounding_box_coords = []

        #          6-----------7
        #         /           /|
        #       4-----------5  |
        #       |           |  |
        #       |           |  |
        #       |  2        |  3
        #       |           | /
        #       0-----------1

        # lower square
        bounding_box_coords.append((xmax, ymin, zmin))  # a (0,1)
        bounding_box_coords.append((xmax, ymax, zmin))
        bounding_box_coords.append((xmax, ymax, zmin))  # b (1,3)
        bounding_box_coords.append((xmin, ymax, zmin))
        bounding_box_coords.append((xmin, ymax, zmin))  # c (3,2)
        bounding_box_coords.append((xmin, ymin, zmin))
        bounding_box_coords.append((xmin, ymin, zmin))  # d (2,0)
        bounding_box_coords.append((xmax, ymin, zmin))
        # upper square
        bounding_box_coords.append((xmax, ymin, zmax))  # e (4,5)
        bounding_box_coords.append((xmax, ymax, zmax))
        bounding_box_coords.append((xmax, ymax, zmax))  # f (5,7)
        bounding_box_coords.append((xmin, ymax, zmax))
        bounding_box_coords.append((xmin, ymax, zmax))  # g (7,6)
        bounding_box_coords.append((xmin, ymin, zmax))
        bounding_box_coords.append((xmin, ymin, zmax))  # h (6,4)
        bounding_box_coords.append((xmax, ymin, zmax))
        # lines from lower square to upper
        bounding_box_coords.append((xmax, ymin, zmin))  # i (0,4)
        bounding_box_coords.append((xmax, ymin, zmax))
        bounding_box_coords.append((xmax, ymax, zmin))  # j (1,5)
        bounding_box_coords.append((xmax, ymax, zmax))
        bounding_box_coords.append((xmin, ymax, zmin))  # k (3,7)
        bounding_box_coords.append((xmin, ymax, zmax))
        bounding_box_coords.append((xmin, ymin, zmin))  # l (2,6)
        bounding_box_coords.append((xmin, ymin, zmax))

        if bpy.context.scene.atom_blend_addon_settings.scaling_cube_mode == 'RGB':
            r = (1, 0, 0, 1)
            g = (0, 1, 0, 1)
            b = (0, 0, 1, 1)

            color_list = [g, g, r, r, g, g, r, r,
                          g, g, r, r, g, g, r, r,
                          b, b, b, b, b, b, b, b]
        else:
            col_struct = bpy.context.scene.atom_blend_addon_settings.scaling_cube_uniform_color
            color = (col_struct[0], col_struct[1], col_struct[2], col_struct[3])
            color_list = [[color] * len(bounding_box_coords)][0]

        # when rendering in viewport, we need to calculate the proj and object matrix, when rendering pictures / videos, we need the matrices from the camera
        if proj_matrix == None:
            proj_matrix = bpy.context.region_data.perspective_matrix
        if object_matrix == None:
            # object_matrix = bpy.data.objects['Origin'].matrix_world
            object_matrix = bpy.data.objects['Scaling Cube'].matrix_world

        ABManagement.get_nearest_points_metric(self, context, bounding_box_coords)

        gpu.state.line_width_set(bpy.context.scene.atom_blend_addon_settings.scaling_cube_line_width)
        batch = batch_for_shader(line_shader, 'LINES', {"position": bounding_box_coords, "color": color_list})
        line_shader.uniform_float('projection_matrix', proj_matrix)
        line_shader.uniform_float('object_matrix', object_matrix)
        # line_shader.uniform_float('color', (1,0,0,1))
        batch.draw(line_shader)

    def get_nearest_points_metric(self, context, bbc):
        def round_width(width):
            if context.scene.atom_blend_addon_settings.scaling_cube_round:
                digits = context.scene.atom_blend_addon_settings.scaling_cube_round_digits
                width = round(width, digits)

                if width % 1 == 0:  # check if the decimal part is 0, if yes cut it off. e.g. 100.0 -> 100
                    width = int(width)

            return width

        # get the view matrix of the current view space view (in order to get the position of the "viewport camera") and calculate the nearest x, y and z axis
        v3d = [a for a in bpy.context.screen.areas if a.type == 'VIEW_3D'][0]
        r3d = v3d.spaces[0].region_3d
        view_mat = r3d.view_matrix.inverted()
        loc, rot, sca = view_mat.decompose()

        bbc_v = [mathutils.Vector(x) for x in bbc]

        # scaling box scale
        scale = context.scene.atom_blend_addon_settings.scaling_cube_scale

        # calculate nearest y axis and draw text for y width
        a = bbc_v[0] + bbc_v[1]
        a /= 2.0
        a_len = (loc - a).length

        c = bbc_v[4] + bbc_v[5]
        c /= 2.0
        c_len = (loc - c).length

        # y
        y_width = ABGlobals.max_y - ABGlobals.min_y
        y_width = round_width(y_width * scale[1])

        if a_len <= c_len:
            ABManagement.draw_text(self, context, bbc_v[0], bbc_v[1], str(y_width) + ' nm')
        else:
            ABManagement.draw_text(self, context, bbc_v[4], bbc_v[5], str(y_width) + ' nm')

        # calculate nearest x axis and draw text for x width
        b = bbc_v[1] + bbc_v[3]
        b /= 2.0
        b_len = (loc - b).length

        d = bbc_v[6] + bbc_v[7]
        d /= 2.0
        d_len = (loc - d).length

        #x
        x_width = ABGlobals.max_x - ABGlobals.min_x
        x_width = round_width(x_width * scale[0])

        if b_len <= d_len:
            ABManagement.draw_text(self, context, bbc_v[1], bbc_v[3], str(x_width) + ' nm')
        else:
            ABManagement.draw_text(self, context, bbc_v[6], bbc_v[7], str(x_width) + ' nm')

        # calculate nearest z axis and draw text for z width
        z_lenghts = []

        i = bbc_v[16] + bbc_v[17]
        i /= 2.0
        i_len = (loc - i).length
        z_lenghts.append(i_len)

        j = bbc_v[18] + bbc_v[19]
        j /= 2.0
        j_len = (loc - j).length
        z_lenghts.append(j_len)

        k = bbc_v[20] + bbc_v[21]
        k /= 2.0
        k_len = (loc - k).length
        z_lenghts.append(k_len)

        l = bbc_v[22] + bbc_v[23]
        l /= 2.0
        l_len = (loc - l).length
        z_lenghts.append(l_len)

        z_width = ABGlobals.max_z - ABGlobals.min_z
        z_width = round_width(z_width * scale[2])

        min_index = z_lenghts.index(min(z_lenghts))

        if min_index == 0:
            ABManagement.draw_text(self, context, bbc_v[16], bbc_v[17], str(z_width) + ' nm')
        elif min_index == 1:
            ABManagement.draw_text(self, context, bbc_v[18], bbc_v[19], str(z_width) + ' nm')
        elif min_index == 2:
            ABManagement.draw_text(self, context, bbc_v[20], bbc_v[21], str(z_width) + ' nm')
        elif min_index == 3:
            ABManagement.draw_text(self, context, bbc_v[22], bbc_v[23], str(z_width) + ' nm')

    def draw_text(self, context, a, b, text):
        def get_viewport_camera_measurement():
            cam_obj = bpy.context.scene.camera
            cam = cam_obj.data

            # upper_right = cam.view_frame(scene=bpy.context.scene)[0]
            lower_right = cam.view_frame(scene=bpy.context.scene)[1]
            lower_left = cam.view_frame(scene=bpy.context.scene)[2]
            upper_left = cam.view_frame(scene=bpy.context.scene)[3]

            # object space -> world space
            lower_left = cam_obj.matrix_world @ lower_left
            lower_right = cam_obj.matrix_world @ lower_right
            upper_left = cam_obj.matrix_world @ upper_left

            # world space -> screen space
            lower_left_viewport = ABManagement.get_3d_to_2d_viewport(self, lower_left)
            lower_right_viewport = ABManagement.get_3d_to_2d_viewport(self, lower_right)
            upper_left_viewport = ABManagement.get_3d_to_2d_viewport(self, upper_left)

            if lower_left_viewport is None:
                return

            viewport_camera_measurement = mathutils.Vector((lower_right_viewport.x - lower_left_viewport.x, upper_left_viewport.y - lower_left_viewport.y))
            return viewport_camera_measurement

        # function to set a value into relation with the render resolution to map it into the viewport
        def in_relation_y(value):
            render_height = bpy.context.scene.render.resolution_y
            return value / render_height

        # calculates angle between the points a and b in relation to the x-axis
        def calc_angle(a, b):
            delta_x = b[0] - a[0]
            delta_y = b[1] - a[1]

            angle = math.atan2(delta_y, delta_x)

            # make sure font is oriented right
            if a[0] > b[0]:
                angle += math.pi

            return angle

        # calculates position of the scaling cube font (depending on font size it's not exactly (a+b)/2)
        def calc_pos(a, b):
            # len_vec_a_b = math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)  # get length of line
            font_dim = blf.dimensions(font_id, text)
            # print(font_dim, len_vec_a_b, a, b)
            # font_perc = float(font_dim[0] / len_vec_a_b)

            # print(type(a))
            # a_vec = mathutils.Vector((a[0], a[1]))
            # b_vec = mathutils.Vector((b[0], b[1]))
            # pos = a_vec + (b_vec * (0.5 - font_perc))

            a_to_b_vec = b - a
            font_perc = font_dim[0] / a_to_b_vec.length

            if a[0] <= b[0]:
                pos = a_2d + a_to_b_vec * (0.5 - font_perc * 0.5)
                # pos = a_2d + a_to_b_vec * (font_perc * 0.5)
            else:
                pos = b_2d - a_to_b_vec * (0.5 - font_perc * 0.5)
                # pos = a_2d - a_to_b_vec * (font_perc * 0.5)

            # print(len_vec_a_b, font_dim, font_perc, pos)
            return pos

        # mapping the 3d point into the camera space
        def img_writing_3d_to_2d(point_3d):
            scene = bpy.context.scene
            cam = scene.camera
            co_2d = object_utils.world_to_camera_view(scene, cam, point_3d)
            render_scale = scene.render.resolution_percentage / 100
            render_size = (int(scene.render.resolution_x * render_scale),
                           int(scene.render.resolution_y * render_scale))

            x_pos = round(co_2d.x * render_size[0])  # / render_size[0]
            y_pos = round(co_2d.y * render_size[1])  # / render_size[1]

            # return [x_pos, y_pos]
            return mathutils.Vector((x_pos, y_pos))

        # font should rotate with scaling cube
        obj_mat = bpy.data.objects['Scaling Cube'].matrix_world
        a = obj_mat @ a
        b = obj_mat @ b

        font_id = 0
        blf.color(font_id, 0, 0, 0, 1)
        font_size = context.scene.atom_blend_addon_settings.scaling_cube_font_size
        point_3d = (a + b) * 0.5
        angle = 0

        if ABGlobals.currently_writing_img: # write picture
            scene = bpy.context.scene
            cam = scene.camera

            # mapping the 3d point into the camera space
            if bpy.context.scene.atom_blend_addon_settings.scaling_cube_rotate_font:
                a_2d = img_writing_3d_to_2d(a)
                b_2d = img_writing_3d_to_2d(b)

                pos = calc_pos(a_2d, b_2d)

                angle = calc_angle(a_2d, b_2d)
            else:
                pos = img_writing_3d_to_2d(point_3d)

            font_size = context.scene.atom_blend_addon_settings.scaling_cube_font_size
            blf.size(font_id, font_size)

            # point_2d = [x_pos, y_pos]
            point_2d = [pos[0], pos[1]]

            # point_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, tuple_point_3d)
            # ui_scale = bpy.context.preferences.system.ui_scale
        else:  ### viewport
            if bpy.context.scene.atom_blend_addon_settings.scaling_cube_rotate_font:
                a_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, a)
                b_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, b)

                if a_2d is None or b_2d is None:
                    return


                pos = calc_pos(a_2d, b_2d)

                # a_to_b_vec = b_2d - a_2d
                # pos = a_2d + a_to_b_vec * 0.3
                # perc = blf.dimensions

                angle = calc_angle(a_2d, b_2d)
            else:
                # pos = img_writing_3d_to_2d(point_3d)
                pos = bpy_extras.view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, point_3d)

            # map font size to viewport
            if context.space_data.region_3d.view_perspective == 'CAMERA': # camera preview
                viewport_camera_measurement = get_viewport_camera_measurement()
                font_size = in_relation_y(context.scene.atom_blend_addon_settings.scaling_cube_font_size) * viewport_camera_measurement.y
                blf.size(font_id, font_size)
            else:
                font_size = int(context.scene.atom_blend_addon_settings.scaling_cube_font_size / 2)
                blf.size(font_id, font_size)

            # text_dim = blf.dimensions(font_id, text)
            # text_dim = mathutils.Vector(text_dim) / 2.0
            # point_3d[0] -= text_dim[0]
            # point_3d -= mathutils.Vector((text_dim[0], text_dim[1], 0))

            point_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, point_3d)
            point_2d = pos

            if point_2d is None:
                return

        blf.enable(font_id, blf.ROTATION)
        # blf.size(font_id, 20.0, font_size)
        blf.rotation(font_id, angle)
        blf.position(font_id, point_2d[0], point_2d[1], 0)
        blf.draw(font_id, text)
        blf.disable(font_id, blf.ROTATION)

    def render(self, context):
        cache = ABManagement.cache
        shader = cache['shader']

        if len(ABGlobals.atom_color_list) != len(ABGlobals.atom_coords):
            # print('ATOM COLOR LIST', ABGlobals.atom_color_list)
            # print('ATOM COORDS', ABGlobals.atom_coords)
            raise Exception("len atom cols != len atom coords", len(ABGlobals.atom_color_list), len(ABGlobals.atom_coords))

        # set background color
        # if context.space_data.region_3d.view_perspective == 'PERSP' or context.space_data.region_3d.view_perspective == 'ORTHO':
        #     bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0.051, 0.051, 0.051, 1)

        # elif context.space_data.region_3d.view_perspective == 'CAMERA':
        #     background_color = bpy.context.scene.atom_blend_addon_settings.background_color
        #     bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = background_color
        if (len(ABGlobals.atom_coords) != len(ABGlobals.atom_color_list)) or (
                len(ABGlobals.atom_coords) != len(ABGlobals.point_size_list)) or (
                len(ABGlobals.atom_color_list) != len(ABGlobals.point_size_list)):
            print(len(ABGlobals.atom_coords), len(ABGlobals.atom_color_list), len(ABGlobals.point_size_list))

        # print('position', ABGlobals.atom_coords)
        # print('color', ABGlobals.atom_color_list)
        # print('point size', ABGlobals.point_size_list)
        batch = batch_for_shader(shader, 'POINTS', {'position': ABGlobals.atom_coords, 'color': ABGlobals.atom_color_list, 'ps': ABGlobals.point_size_list})

        # uniform preparations
        proj_matrix = bpy.context.region_data.perspective_matrix
        object_matrix = bpy.data.objects['Top'].matrix_world

        # pass uniforms to shader
        shader.bind()
        shader.uniform_float('projection_matrix', proj_matrix)
        shader.uniform_float('object_matrix', object_matrix)
        batch.draw(shader)

    def save_image(self, context, cur_frame=''):
        ABGlobals.currently_writing_img = True

        start = time.perf_counter()

        cache = ABManagement.cache
        scene = context.scene

        render = scene.render
        width = int(render.resolution_x)
        height = int(render.resolution_y)

        view_matrix = mathutils.Matrix([
            [2 / width, 0, 0, -1],
            [0, 2 / height, 0, -1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]])

        # create buffer
        offscreen = gpu.types.GPUOffScreen(width, height)
        gpu.state.blend_set('ALPHA')
        gpu.state.program_point_size_set(True)

        with offscreen.bind():
            fb = gpu.state.active_framebuffer_get()
            if context.scene.atom_blend_addon_settings.transparent_background:
                background_color = [1, 1, 1, 0]
            else:
                background_color = context.scene.atom_blend_addon_settings.background_color

            fb.clear(color=background_color, depth=1.0)

            gpu.state.depth_test_set('LESS_EQUAL')
            gpu.state.depth_mask_set(True)
            gpu.matrix.load_matrix(view_matrix)
            gpu.matrix.load_projection_matrix(mathutils.Matrix.Identity(4))

            view_matrix = scene.camera.matrix_world.inverted()
            camera_matrix = scene.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(), x=width, y=height, scale_x=render.pixel_aspect_x, scale_y=render.pixel_aspect_y)
            proj_matrix = camera_matrix @ view_matrix
            object_matrix = bpy.data.objects['Top'].matrix_world

            # draw shader
            shader = cache['shader']

            # adapting the point size when writing image because the points are much smaller than in viewport when rendering for some reason
            adapted_point_size = [i * 2.5 for i in ABGlobals.point_size_list]

            # offscreen.draw_view3d(scene, context.view_layer, context.space_data, context.region, view_matrix, proj_matrix, do_color_management=True)

            batch = batch_for_shader(shader, 'POINTS', {'position': ABGlobals.atom_coords, 'color': ABGlobals.atom_color_list, 'ps': adapted_point_size})

            shader.bind()
            shader.uniform_float('projection_matrix', proj_matrix)
            shader.uniform_float('object_matrix', object_matrix)
            batch.draw(shader)

            # ABManagement.render_metric(self, context)
            if bpy.context.scene.atom_blend_addon_settings.scaling_cube:
                ABManagement.create_bounding_box(self, context, proj_matrix=proj_matrix)

            ABManagement.create_legend(self, context, render_img=True)

            buffer = fb.read_color(0, 0, width, height, 4, 0, 'UBYTE')
            buffer.dimensions = width * height * 4

        offscreen.free()

        # create and save image
        render_name = 'render_output'
        if render_name not in bpy.data.images:
            bpy.data.images.new(render_name, width, height, alpha=True)
        image = bpy.data.images[render_name]
        image.scale(width, height)

        image.pixels = [v / 255 for v in buffer]

        # actually save image
        path = bpy.data.scenes["Scene"].render.filepath

        # file_format = bpy.data.scenes["Scene"].render.image_settings.file_format
        # print(ABGlobals.dataset_name, str(cur_frame), file_format.lower())
        filename = ABGlobals.dataset_name + '_frame_' + str(cur_frame) + '.png'  # file_format.lower()
        # if path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff')):
        #     render_path = path
        #     image.file_format = file_format.upper() #render_path.split('.')[-1].upper()  # 'PNG'
        # elif path.lower().endswith('.avi'):
        #     render_path = path
        #     image.file_format = 'PNG' #file_format.upper()
        # else:
        #     render_path = path + '//' + filename
        #     image.file_format = file_format.upper() # render_path.split('.')[-1].upper()  # 'PNG'

        if not ABGlobals.render_frame:
            path = os.path.split(path)[0]
            path = path + '//' + filename

        if path.lower().endswith(('.png')):
            render_path = path
        else:
            render_path = path + '.png'

        image.file_format = 'PNG'

        render_path = r'%s' % render_path

        file_format = context.scene.atom_blend_addon_settings.file_format
        # file_format = bpy.data.scenes["Scene"].render.image_settings.file_format
        filename = ABGlobals.dataset_name + '_frame_' + str(cur_frame) + '.' + file_format.lower()

        if file_format == 'PNG':
            image.file_format = 'PNG'
            if os.path.splitext(path)[1].lower() == '.png':  # file ending is already png
                render_path = path
            elif os.path.splitext(path)[1].lower() in ['.png', '.jpg', '.jpeg', '.tiff']:  # file ending is not .png
                render_path = path + '.png'
            else:  # there is no file name, just a directory -> add file name and format
                render_path = path + filename
        elif file_format == 'JPEG':
            image.file_format = 'JPEG'
            if os.path.splitext(path)[1].lower() == '.jpg' or os.path.splitext(path)[1].lower() == '.jpeg':
                render_path = path
            elif os.path.splitext(path)[1].lower() in ['.png', '.jpg', '.jpeg', '.tiff']:
                render_path = path + '.jpg'
            else:
                render_path = path + filename
        else:
            image.file_format = 'TIFF'
            if os.path.splitext(path)[1].lower() == '.tiff':
                render_path = path
            elif os.path.splitext(path)[1].lower() in ['.png', '.jpg', '.jpeg', '.tiff']:
                render_path = path + '.tiff'
            else:
                render_path = path + filename

        # if path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff')):
        #     render_path = path
        # else:
        #     render_path = path + '//' + filename

        image.filepath_raw = render_path

        # if os.path.isfile(image.filepath_raw):
        #     os.remove(image.filepath_raw)

        image.save()

        print('Wrote file to ' + render_path)

        gpu.state.depth_mask_set(False)
        ABGlobals.currently_writing_img = False
        return render_path
