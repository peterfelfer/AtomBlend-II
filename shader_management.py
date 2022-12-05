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

        #print(top_x, top_y, top_z)
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
            bpy.ops.object.camera_add(location=(0,0,0))
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
        bpy.data.scenes["Scene"].render.filepath = bpy.data.scenes["Scene"].render.filepath + ABGlobals.dataset_name + '.png'


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

    #def frame_change_handler(self, context):
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
        bounding_box_coords.append((xmax, ymin, zmin)) # a
        bounding_box_coords.append((xmax, ymax, zmin))
        bounding_box_coords.append((xmax, ymax, zmin)) # b
        bounding_box_coords.append((xmin, ymax, zmin))
        bounding_box_coords.append((xmin, ymin, zmin)) # c
        bounding_box_coords.append((xmin, ymax, zmin))
        bounding_box_coords.append((xmax, ymin, zmin)) # d
        bounding_box_coords.append((xmin, ymin, zmin))
        # lines from lower square to upper
        bounding_box_coords.append((xmax, ymin, zmax)) # e
        bounding_box_coords.append((xmax, ymax, zmax))
        bounding_box_coords.append((xmax, ymax, zmax)) # f
        bounding_box_coords.append((xmin, ymax, zmax))
        bounding_box_coords.append((xmin, ymin, zmax)) # g
        bounding_box_coords.append((xmin, ymax, zmax))
        bounding_box_coords.append((xmax, ymin, zmax)) # h
        bounding_box_coords.append((xmin, ymin, zmax))
        # upper square
        bounding_box_coords.append((xmax, ymin, zmin)) # i
        bounding_box_coords.append((xmax, ymin, zmax))
        bounding_box_coords.append((xmax, ymax, zmin)) # j
        bounding_box_coords.append((xmax, ymax, zmax))
        bounding_box_coords.append((xmin, ymax, zmin)) # k
        bounding_box_coords.append((xmin, ymax, zmax))
        bounding_box_coords.append((xmin, ymin, zmin)) # l
        bounding_box_coords.append((xmin, ymin, zmax))

        if bpy.context.scene.atom_blend_addon_settings.scaling_cube_mode == 'RGB':
            r = (1,0,0,1)
            g = (0,1,0,1)
            b = (0,0,1,1)

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

        print(len(color_list), len(bounding_box_coords))

        batch = batch_for_shader(line_shader, 'LINES', {"position": bounding_box_coords, "color": color_list})
        line_shader.uniform_float('projection_matrix', proj_matrix)
        line_shader.uniform_float('object_matrix', object_matrix)
        # line_shader.uniform_float('color', (1,0,0,1))
        batch.draw(line_shader)

    def render_metric(self, context):
        cache = ABManagement.cache
        line_shader = cache['my_line_shader']
        # gpu.state.blend_set('ALPHA')
        # gpu.state.program_point_size_set(True)
        # # gpu.state.depth_mask_set(False)
        # gpu.state.depth_test_set('ALWAYS')

        # coords = [(-50, 0, 0), (50, 0, 0)]
        coords = [(-10, 0, 0), (10, 0, 0)]
        batch = batch_for_shader(line_shader, 'LINES', {"position": coords})

        proj_matrix = bpy.context.region_data.perspective_matrix
        object_matrix = bpy.data.objects['Origin'].matrix_world
        view_matrix = context.scene.camera.matrix_world.inverted()

        line_shader.bind()
        line_shader.uniform_float('projection_matrix', proj_matrix)
        line_shader.uniform_float('object_matrix', object_matrix)
        # line_shader.uniform_float('view_matrix', view_matrix)
        batch.draw(line_shader)

        # draw text
        x_width = ABGlobals.max_x - ABGlobals.min_x
        y_width = ABGlobals.max_y - ABGlobals.min_y
        z_width = ABGlobals.max_z - ABGlobals.min_z
        font_id = 0
        blf.color(font_id, 1, 0, 0, 1)
        # blf.enable(font_id, ROTATION) # 1 == ROTATION
        # blf.rotation(font_id, 90.0)
        # blf.size(font_id, 0.04, 72)
        blf.size(font_id, 20.0, 72)
        blf.position(font_id, 2, 45, 0)
        blf.draw(font_id, 'x: ' + str(x_width) + ' nm')
        blf.position(font_id, 2, 25, 0)
        blf.draw(font_id, 'y: ' + str(y_width) + ' nm')
        blf.position(font_id, 2, 5, 0)
        blf.draw(font_id, 'z: ' + str(z_width) + ' nm')
        # blf.disable(font_id, ROTATION)

    '''def render_metric(self, context):
        cache = ABManagement.cache
        line_shader = cache['line_shader']

        gpu.state.blend_set('ALPHA')
        gpu.state.program_point_size_set(True)
        gpu.state.depth_mask_set(False)

        coords = [(-10, 0, 2), (10, 0, 2)]
        # color = [(1.0, 0.0, 0.0, 1.0), (1.0, 0.0, 0.0, 1.0)]

        # batch = batch_for_shader(line_shader, 'LINES', {"pos": coords})
        batch = batch_for_shader(line_shader, 'LINE_STRIP', {"pos": coords})

        line_shader.bind()
        line_shader.uniform_float("color", (1.0, 0.0, 0.0, 1.0))
        # line_shader.uniform_float("lineWidth", 50.0)
        # line_shader.uniform_float("viewportSize", (0,0))
        batch.draw(line_shader)'''


    def render(self, context):
        cache = ABManagement.cache
        shader = cache['shader']

        # gpu.state.blend_set('ALPHA')
        # gpu.state.program_point_size_set(True)
        # gpu.state.depth_mask_set(False)
        # gpu.state.depth_test_set('ALWAYS')

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
        if (len(ABGlobals.atom_coords) != len(ABGlobals.atom_color_list)) or (len(ABGlobals.atom_coords) != len(ABGlobals.point_size_list)) or (len(ABGlobals.atom_color_list) != len(ABGlobals.point_size_list)):
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
        start = time.perf_counter()

        cache = ABManagement.cache
        scene = context.scene

        render = scene.render
        width = int(render.resolution_x)
        height = int(render.resolution_y)

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

        #file_format = bpy.data.scenes["Scene"].render.image_settings.file_format
        #print(ABGlobals.dataset_name, str(cur_frame), file_format.lower())
        filename = ABGlobals.dataset_name + '_frame_' + str(cur_frame) + '.png' #file_format.lower()
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
        #file_format = bpy.data.scenes["Scene"].render.image_settings.file_format
        filename = ABGlobals.dataset_name + '_frame_' + str(cur_frame) + '.' + file_format.lower()

        if file_format == 'PNG':
            image.file_format  = 'PNG'
            if os.path.splitext(path)[1].lower() == '.png': # file ending is already png
                render_path = path
            elif os.path.splitext(path)[1].lower() in ['.png', '.jpg', '.jpeg', '.tiff']: # file ending is not .png
                render_path = path + '.png'
            else: # there is no file name, just a directory -> add file name and format
                render_path = path + filename
        elif file_format == 'JPEG':
            image.file_format  = 'JPEG'
            if os.path.splitext(path)[1].lower() == '.jpg' or os.path.splitext(path)[1].lower() == '.jpeg':
                render_path = path
            elif os.path.splitext(path)[1].lower() in ['.png', '.jpg', '.jpeg', '.tiff']:
                render_path = path + '.jpg'
            else:
                render_path = path + filename
        else:
            image.file_format  = 'TIFF'
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
        return render_path
