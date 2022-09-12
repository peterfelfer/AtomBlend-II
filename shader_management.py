import bpy
import gpu
from gpu.types import GPUShader
from .shaders import *
# from .read_data import AtomBlendAddon
from .read_data import *
from gpu_extras.batch import batch_for_shader
from .globals import ABGlobals
import numpy as np


class ABManagement:
    cache = {}

    def init_shader(self, context):
        # print('INIT')
        # init shader
        shader = GPUShader(ABShaders.vertex_shader_simple, ABShaders.fragment_shader_simple)

        # # shader input
        ABGlobals.atom_color_list = []
        for elem_name in ABGlobals.all_elements_by_name:
            # print(elem_name, ABGlobals.all_elements_by_name[elem_name]['num_displayed'])
            # elem_amount = len(ABGlobals.all_elements_by_name[elem_name]['coordinates'])
            # col_struct = bpy.context.scene.color_settings[elem_name].color
            # col = (col_struct[0], col_struct[1], col_struct[2], col_struct[3])
            # ABGlobals.atom_color_list.append([col] * elem_amount)

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
        ABManagement.handle = bpy.types.SpaceView3D.draw_handler_add(ABManagement.handler, (self, context), 'WINDOW', 'POST_VIEW')

        # create empty to move the atom tip to the center (0,0,0)
        top_x = (ABGlobals.max_x + ABGlobals.min_x) / 2
        top_y = (ABGlobals.max_y + ABGlobals.min_y) / 2
        top_z = (ABGlobals.max_z + ABGlobals.min_z) / 2

        print(top_x, top_y, top_z)
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
        bpy.data.curves['BezierCircle'].path_duration = context.scene.atom_blend_addon_settings.frame_amount
        bpy.data.scenes["Scene"].frame_end = context.scene.atom_blend_addon_settings.frame_amount

        # init point sizes
        num_displayed = ABGlobals.all_elements_by_name[elem_name]['num_displayed']
        point_size = bpy.context.scene.color_settings[elem_name].point_size
        ABGlobals.point_size_list = [point_size] * num_displayed

        # save in cache
        cache = ABManagement.cache
        cache['shader'] = shader
        cache['camera'] = bpy.context.scene.camera

    def handler(self, context):
        # print('handler!')
        # update camera position in addon (if the camera is moved via viewport)
        cam_loc = bpy.data.objects["Camera"].location
        context.scene.atom_blend_addon_settings.camera_location_x_frame = cam_loc[0]
        context.scene.atom_blend_addon_settings.camera_location_y_frame = cam_loc[1]
        context.scene.atom_blend_addon_settings.camera_location_z_frame = cam_loc[2]

        # render frame
        ABManagement.render(self, context)

    def render(self, context):
        cache = ABManagement.cache
        shader = cache['shader']

        gpu.state.blend_set('ALPHA')
        gpu.state.program_point_size_set(True)
        gpu.state.depth_mask_set(False)

        if len(ABGlobals.atom_color_list) != len(ABGlobals.atom_coords):
            # print('ATOM COLOR LIST', ABGlobals.atom_color_list)
            # print('ATOM COORDS', ABGlobals.atom_coords)
            raise Exception("len atom cols != len atom coords", len(ABGlobals.atom_color_list), len(ABGlobals.atom_coords))

        # print(len(ABGlobals.atom_coords), len(ABGlobals.atom_color_list), len(ABGlobals.point_size_list))
        batch = batch_for_shader(shader, 'POINTS', {'position': ABGlobals.atom_coords, 'color': ABGlobals.atom_color_list, 'ps': ABGlobals.point_size_list})

        # uniform preparations
        proj_matrix = bpy.context.region_data.perspective_matrix
        object_matrix = bpy.data.objects['Top'].matrix_world

        # pass uniforms to shader
        shader.bind()
        shader.uniform_float('projection_matrix', proj_matrix)
        shader.uniform_float('object_matrix', object_matrix)
        shader.uniform_float('alpha_radius', 1.0)
        batch.draw(shader)

    def save_image(self, context, cur_frame=''):
        cache = ABManagement.cache
        scene = context.scene

        render = scene.render
        width = int(render.resolution_x)
        height = int(render.resolution_y)

        # create buffer
        offscreen = gpu.types.GPUOffScreen(width, height)
        gpu.state.blend_set('ALPHA')
        gpu.state.program_point_size_set(True)
        gpu.state.depth_mask_set(False)

        with offscreen.bind():
            fb = gpu.state.active_framebuffer_get()
            background_color = context.scene.atom_blend_addon_settings.background_color

            fb.clear(color=background_color, depth=1.0)

            view_matrix = scene.camera.matrix_world.inverted()
            camera_matrix = scene.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(), x=width, y=height, scale_x=render.pixel_aspect_x, scale_y=render.pixel_aspect_y)
            proj_matrix = camera_matrix @ view_matrix
            object_matrix = bpy.data.objects['Top'].matrix_world

            # draw shader
            shader = cache['shader']

            # adapting the point size when writing image because the points are much smaller than in viewport when rendering for some reason
            adapted_point_size = [i * 2.5 for i in ABGlobals.point_size_list]

            batch = batch_for_shader(shader, 'POINTS', {'position': ABGlobals.atom_coords, 'color': ABGlobals.atom_color_list, 'ps': adapted_point_size})

            shader.bind()
            shader.uniform_float('projection_matrix', proj_matrix)
            shader.uniform_float('object_matrix', object_matrix)
            shader.uniform_float('alpha_radius', 1.0)
            batch.draw(shader)

            buffer = fb.read_color(0, 0, width, height, 4, 0, 'UBYTE')
            buffer.dimensions = width * height * 4

        offscreen.free()

        # create and save image
        render_name = 'render_output'
        if render_name not in bpy.data.images:
            bpy.data.images.new(render_name, width, height)
        image = bpy.data.images[render_name]
        image.scale(width, height)

        image.pixels = [v / 255 for v in buffer]

        # actually save image

        render_path = os.path.dirname(bpy.data.scenes["Scene"].render.filepath) + '\\render_' + str(cur_frame) + '.png'
        image.file_format = 'PNG'
        image.filepath_raw = render_path
        image.save()