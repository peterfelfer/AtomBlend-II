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
import mathutils
import bpy_extras.object_utils as object_utils


class ABManagement:
    cache = {}

    def init(self, context):
        # --- init shader ---
        shader = GPUShader(ABShaders.vertex_shader_simple, ABShaders.fragment_shader_simple)
        # line_shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        # line_shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        my_line_shader = GPUShader(ABShaders.metric_vertex_shader, ABShaders.metric_fragment_shader)

        # shader input
        ABGlobals.atom_color_list = []
        for elem_name in ABGlobals.all_elements_by_name:
            # print(elem_name, ABGlobals.all_elements_by_name[elem_name]['num_displayed'])
            # elem_amount = len(ABGlobals.all_elements_by_name[elem_name]['coordinates'])
            # col_struct = bpy.context.scene.color_settings[elem_name].color
            # col = (col_struct[0], col_struct[1], col_struct[2], col_struct[3])
            # ABGlobals.atom_color_list.append([col] * elem_amount)

            # init point sizes
            ABGlobals.point_size_list = []

            for elem_name in ABGlobals.all_elements_by_name:
                num_displayed = ABGlobals.all_elements_by_name[elem_name]['num_displayed']
                point_size = bpy.context.scene.color_settings[elem_name].point_size
                ABGlobals.point_size_list.append([point_size] * num_displayed)
                # print(elem_name, point_size, num_displayed, len(ABGlobals.point_size_list))

            # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
            if len(ABGlobals.point_size_list) > 0 and isinstance(ABGlobals.point_size_list[0], list):
                ABGlobals.point_size_list = [x for xs in ABGlobals.point_size_list for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

            bpy.context.scene.color_settings[elem_name].perc_displayed = bpy.context.scene.atom_blend_addon_settings.vertex_percentage
        '''
        # check if we have a list for each element for the atom coords and atom color list
        # -> flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if isinstance(ABGlobals.atom_coords[0], list):
            ABGlobals.atom_coords = [x for xs in ABGlobals.atom_coords for x in xs] #https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

        if isinstance(ABGlobals.atom_color_list[0], list):
            ABGlobals.atom_color_list = [x for xs in ABGlobals.atom_color_list for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

        if len(ABGlobals.atom_color_list) != len(ABGlobals.atom_coords):
            # print('ATOM COLOR LIST', ABGlobals.atom_color_list)
            # print('ATOM COORDS', ABGlobals.atom_coords)
            raise Exception("len atom cols != len atom coords", len(ABGlobals.atom_color_list), len(ABGlobals.atom_coords))
        # batch = batch_for_shader(shader, 'POINTS', {'position': ABGlobals.atom_coords, 'color': ABGlobals.atom_color_list, })
        vertices = ((0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1))
        col_list = ((1,1,1,1), (1,1,1,1),(1,1,1,1), (1,1,1,1,))
        # indices = ((0, 1, 2), (2, 1, 3))
        print('coord list', ABGlobals.atom_coords)
        print('col list', ABGlobals.atom_color_list)
        batch = batch_for_shader(shader, 'POINTS', {'position': ABGlobals.atom_coords, 'color': ABGlobals.atom_color_list, })
        # batch = batch_for_shader(shader, 'POINTS', {'position': vertices, 'color': col_list, })
        '''
        # add draw handler that will be called every time this region in this space type will be drawn
        # ABManagement.handle = bpy.types.SpaceView3D.draw_handler_add(ABManagement.handler, (self, context), 'WINDOW', 'POST_VIEW')
        ABManagement.handle = bpy.types.SpaceView3D.draw_handler_add(ABManagement.handler, (self, context), 'WINDOW', 'POST_PIXEL')

        # --- init other things needed for shader drawing ---
        # create empty to move the atom tip to the center (0,0,0)
        top_x = (ABGlobals.max_x + ABGlobals.min_x) / 2
        top_y = (ABGlobals.max_y + ABGlobals.min_y) / 2
        top_z = (ABGlobals.max_z + ABGlobals.min_z) / 2

        # print(top_x, top_y, top_z)
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, top_z))
        bpy.data.objects['Empty'].name = 'Top'

        # create empty representing the approximate center of the atom tip
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(top_x, top_y, 0))
        bpy.data.objects['Empty'].name = 'Center'

        # create empty representing the origin (0,0,0)
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        bpy.data.objects['Empty'].name = 'Origin'

        # rotate tip 180 degrees around x axis
        bpy.data.objects['Top'].rotation_euler[0] = math.pi

        # set camera if it doesn't exist yet
        if bpy.context.scene.camera is None:
            # calculate camera position
            bpy.ops.object.camera_add(location=(0, 0, 0))
            bpy.data.objects["Camera"].rotation_euler = (-0.5 * math.pi, 0, 0)
            # TODO: disable for viewport

        # preparations for video rendering
        bpy.ops.curve.primitive_bezier_circle_add(radius=100, location=bpy.data.objects['Center'].location)
        bpy.data.objects['BezierCircle'].name = 'Camera path'
        # constraint = bpy.data.objects['Camera'].constraints.new('COPY_LOCATION')
        # constraint.target = bpy.data.objects['Origin']
        constraint = bpy.data.objects['Camera'].constraints.new('FOLLOW_PATH')
        constraint.target = bpy.data.objects['Camera path']
        bpy.context.view_layer.objects.active = bpy.data.objects['Camera']
        bpy.ops.constraint.followpath_path_animate(constraint='Follow Path')
        constraint = bpy.data.objects['Camera'].constraints.new('TRACK_TO')
        constraint.target = bpy.data.objects['Center']
        bpy.data.curves['BezierCircle'].path_duration = context.scene.atom_blend_addon_settings.frames
        bpy.data.scenes["Scene"].frame_end = context.scene.atom_blend_addon_settings.frames
        bpy.data.cameras["Camera"].clip_end = 5000

        # init point sizes
        # num_displayed = ABGlobals.all_elements_by_name[elem_name]['num_displayed']
        # point_size = bpy.context.scene.color_settings[elem_name].point_size
        # ABGlobals.point_size_list = [point_size] * num_displayed

        # save in cache
        cache = ABManagement.cache
        cache['shader'] = shader
        cache['my_line_shader'] = my_line_shader
        cache['camera'] = bpy.context.scene.camera

        # set background color
        bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = [1.0, 1.0, 1.0, 1.0]

        # init camera distance (-> camera path scale)
        bpy.data.objects['Camera path'].scale = (3.0, 3.0, 3.0)

        # hide objects in viewport
        bpy.data.objects['Camera'].hide_viewport = True
        bpy.data.objects['Camera path'].hide_viewport = True
        bpy.data.objects['Center'].hide_viewport = True
        bpy.data.objects['Top'].hide_viewport = True
        bpy.data.objects['Origin'].hide_viewport = True

        # set default path
        bpy.data.scenes["Scene"].render.filepath = bpy.data.scenes[
                                                       "Scene"].render.filepath + ABGlobals.dataset_name + '.png'

    def handler(self, context):
        # print('handler!')
        # update camera position in addon (if the camera is moved via viewport)
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

        gpu.state.depth_mask_set(False)

    # def frame_change_handler(self, context):
    #    pass

    def create_bounding_box(self, context, proj_matrix=None, object_matrix=None):
        cache = ABManagement.cache
        line_shader = cache['my_line_shader']
        xmin = ABGlobals.min_x
        xmax = ABGlobals.max_x
        ymin = ABGlobals.min_y
        ymax = ABGlobals.max_y
        zmin = ABGlobals.min_z - bpy.data.objects['Top'].location[2]
        zmax = ABGlobals.max_z - bpy.data.objects['Top'].location[2]
        bounding_box_coords = []

        # lower square
        bounding_box_coords.append((xmax, ymin, zmin))  # a
        bounding_box_coords.append((xmax, ymax, zmin))
        bounding_box_coords.append((xmax, ymax, zmin))  # b
        bounding_box_coords.append((xmin, ymax, zmin))
        bounding_box_coords.append((xmin, ymin, zmin))  # c
        bounding_box_coords.append((xmin, ymax, zmin))
        bounding_box_coords.append((xmax, ymin, zmin))  # d
        bounding_box_coords.append((xmin, ymin, zmin))
        # upper square
        bounding_box_coords.append((xmax, ymin, zmax))  # e
        bounding_box_coords.append((xmax, ymax, zmax))
        bounding_box_coords.append((xmax, ymax, zmax))  # f
        bounding_box_coords.append((xmin, ymax, zmax))
        bounding_box_coords.append((xmin, ymin, zmax))  # g
        bounding_box_coords.append((xmin, ymax, zmax))
        bounding_box_coords.append((xmax, ymin, zmax))  # h
        bounding_box_coords.append((xmin, ymin, zmax))
        # lines from lower square to upper
        bounding_box_coords.append((xmax, ymin, zmin))  # i
        bounding_box_coords.append((xmax, ymin, zmax))
        bounding_box_coords.append((xmax, ymax, zmin))  # j
        bounding_box_coords.append((xmax, ymax, zmax))
        bounding_box_coords.append((xmin, ymax, zmin))  # k
        bounding_box_coords.append((xmin, ymax, zmax))
        bounding_box_coords.append((xmin, ymin, zmin))  # l
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
            print(color_list)

        # when rendering in viewport, we need to calculate the proj and object matrix, when rendering pictures / videos, we need the matrices from the camera
        if proj_matrix == None:
            proj_matrix = bpy.context.region_data.perspective_matrix
        if object_matrix == None:
            object_matrix = bpy.data.objects['Origin'].matrix_world

        ABManagement.get_nearest_points_metric(self, context, bounding_box_coords)

        gpu.state.line_width_set(bpy.context.scene.atom_blend_addon_settings.scaling_cube_line_width)
        batch = batch_for_shader(line_shader, 'LINES', {"position": bounding_box_coords, "color": color_list})
        line_shader.uniform_float('projection_matrix', proj_matrix)
        line_shader.uniform_float('object_matrix', object_matrix)
        # line_shader.uniform_float('color', (1,0,0,1))
        batch.draw(line_shader)

    def get_nearest_points_metric(self, context, bbc):
        # get the view matrix of the current view space view (in order to get the position of the "viewport camera") and calculate the nearest x, y and z axis
        v3d = [a for a in bpy.context.screen.areas if a.type == 'VIEW_3D'][0]
        r3d = v3d.spaces[0].region_3d
        view_mat = r3d.view_matrix.inverted()
        loc, rot, sca = view_mat.decompose()

        bbc_v = [mathutils.Vector(x) for x in bbc]

        # calculate nearest x axis and draw text for x width
        a = bbc_v[0] + bbc_v[1]
        a /= 2.0
        a_len = (loc - a).length

        c = bbc_v[4] + bbc_v[5]
        c /= 2.0
        c_len = (loc - c).length

        x_width = round(ABGlobals.max_x - ABGlobals.min_x)
        if a_len <= c_len:
            ABManagement.draw_text(self, context, a, str(x_width) + ' nm')
        else:
            ABManagement.draw_text(self, context, c, str(x_width) + ' nm')

        # calculate nearest y axis and draw text for y width
        b = bbc_v[2] + bbc_v[3]
        b /= 2.0
        b_len = (loc - b).length

        d = bbc_v[6] + bbc_v[7]
        d /= 2.0
        d_len = (loc - d).length

        y_width = round(ABGlobals.max_y - ABGlobals.min_y)
        if b_len <= d_len:
            ABManagement.draw_text(self, context, b, str(y_width) + ' nm')
        else:
            ABManagement.draw_text(self, context, d, str(y_width) + ' nm')

        # calculate nearest z axis and draw text for z width
        z_pos = []
        z_lenghts = []

        i = bbc_v[16] + bbc_v[17]
        i /= 2.0
        i_len = (loc - i).length
        z_pos.append(i)
        z_lenghts.append(i_len)

        j = bbc_v[18] + bbc_v[19]
        j /= 2.0
        j_len = (loc - j).length
        z_pos.append(j)
        z_lenghts.append(j_len)

        k = bbc_v[20] + bbc_v[21]
        k /= 2.0
        k_len = (loc - k).length
        z_pos.append(k)
        z_lenghts.append(k_len)

        l = bbc_v[22] + bbc_v[23]
        l /= 2.0
        l_len = (loc - l).length
        z_pos.append(l)
        z_lenghts.append(l_len)

        z_width = round(ABGlobals.max_z - ABGlobals.min_z)
        min_index = z_lenghts.index(min(z_lenghts))
        min_pos = z_pos[min_index]

        ABManagement.draw_text(self, context, min_pos, str(z_width) + ' nm')

    def draw_text(self, context, point_3d, text):
        font_id = 0
        blf.color(font_id, 0, 0, 0, 1)
        font_size = context.scene.atom_blend_addon_settings.scaling_cube_font_size

        if ABGlobals.currently_writing_img: # write picture
            scene = bpy.context.scene
            cam = scene.camera

            # mapping the 3d point into the camera space
            co_2d = object_utils.world_to_camera_view(scene, cam, point_3d)
            render_scale = scene.render.resolution_percentage / 100
            render_size = (int(scene.render.resolution_x * render_scale),
                           int(scene.render.resolution_y * render_scale))

            x_pos = round(co_2d.x * render_size[0])  # / render_size[0]
            y_pos = round(co_2d.y * render_size[1])  # / render_size[1]

            point_2d = [x_pos, y_pos]

            # point_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, tuple_point_3d)
            # ui_scale = bpy.context.preferences.system.ui_scale
        else:  ### viewport
            point_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, point_3d)

        if point_2d is not None: # point_2d is None if position is behind camera
            blf.size(font_id, 20.0, font_size)
            blf.position(font_id, point_2d[0], point_2d[1], 0)
            blf.draw(font_id, text)

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
        #
        # elif context.space_data.region_3d.view_perspective == 'CAMERA':
        #     background_color = bpy.context.scene.atom_blend_addon_settings.background_color
        #     bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = background_color
        if (len(ABGlobals.atom_coords) != len(ABGlobals.atom_color_list)) or (
                len(ABGlobals.atom_coords) != len(ABGlobals.point_size_list)) or (
                len(ABGlobals.atom_color_list) != len(ABGlobals.point_size_list)):
            print(len(ABGlobals.atom_coords), len(ABGlobals.atom_color_list), len(ABGlobals.point_size_list))
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
            ABManagement.create_bounding_box(self, context, proj_matrix=proj_matrix)

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
