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
        '''
        # if len(ABGlobals.atom_color_list) != len(ABGlobals.atom_coords):
        #     # print('ATOM COLOR LIST', ABGlobals.atom_color_list)
        #     # print('ATOM COORDS', ABGlobals.atom_coords)
        #     raise Exception("len atom cols != len atom coords", len(ABGlobals.atom_color_list), len(ABGlobals.atom_coords))
        # batch = batch_for_shader(shader, 'POINTS', {'position': ABGlobals.atom_coords})

        vertices = ((0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1))
        indices = ((0, 1, 2), (2, 1, 3))
        batch = batch_for_shader(shader, 'TRIS', {'position': vertices}, indices=indices)

        # add draw handler that will be called every time this region in this space type will be drawn
        ABManagement.handle = bpy.types.SpaceView3D.draw_handler_add(ABManagement.handler, (self, context), 'WINDOW', 'POST_VIEW')

        # create empty object for object matrix
        bpy.ops.object.empty_add(type='PLAIN_AXES')

        # set camera if it doesn't exist yet
        if bpy.context.scene.camera is None:
            bpy.ops.object.camera_add(location=(0.0, 0.0, 8.0))
            # TODO: disable for viewport

        # save in cache
        cache = ABManagement.cache
        cache['shader'] = shader
        cache['batch'] = batch
        cache['camera'] = bpy.context.scene.camera

    def handler(self, context):
        # print('HANDLER')
        ABManagement.render(self, context)

    def render(self, context):
        cache = ABManagement.cache
        shader = cache['shader']

        gpu.state.blend_set('ALPHA')
        gpu.state.program_point_size_set(True)
        gpu.state.depth_mask_set(True)

        vertices = ((0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1))
        indices = ((0, 1, 2), (2, 1, 3))
        batch = batch_for_shader(shader, 'TRIS', {'position': vertices}, indices=indices)

        # uniform preparations
        proj_matrix = bpy.context.region_data.perspective_matrix
        object_matrix = bpy.data.objects['Empty'].matrix_world

        # pass uniforms to shader
        shader.bind()
        shader.uniform_float('projection_matrix', proj_matrix)
        shader.uniform_float('object_matrix', object_matrix)
        shader.uniform_float('point_size', ABGlobals.point_size)
        shader.uniform_float('alpha_radius', 1.0)
        batch.draw(shader)

    def save_image(self, context):
        cache = ABManagement.cache
        scene = context.scene
        view_layer = context.view_layer
        space = context.space_data
        region = context.region

        render = scene.render
        width = int(render.resolution_x)
        height = int(render.resolution_y)

        # create buffer
        offscreen = gpu.types.GPUOffScreen(width, height)
        gpu.state.blend_set('ALPHA')
        gpu.state.program_point_size_set(True)
        gpu.state.depth_mask_set(True)

        with offscreen.bind():
            fb = gpu.state.active_framebuffer_get()
            fb.clear(color=(1.0, 0.0, 0.0, 0.0))

            view_matrix = scene.camera.matrix_world.inverted()
            proj_matrix = scene.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(), x=width, y=height, scale_x=render.pixel_aspect_x, scale_y=render.pixel_aspect_y)

            bpy.ops.object.empty_add(type='PLAIN_AXES')
            object_matrix = bpy.data.objects['Empty'].matrix_world

            # draw shader
            shader = cache['shader']
            vertices = ((0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1))
            indices = ((0, 1, 2), (2, 1, 3))
            batch = batch_for_shader(shader, 'TRIS', {'position': vertices}, indices=indices)
            shader.bind()
            shader.uniform_float('projection_matrix', proj_matrix)
            # shader.uniform_float('view_matrix', view_matrix)
            shader.uniform_float('object_matrix', object_matrix)
            shader.uniform_float('point_size', ABGlobals.point_size)
            shader.uniform_float('alpha_radius', 1.0)
            batch.draw(shader)

            # draw scene into offscreen
            offscreen.draw_view3d(scene, view_layer, space, region, view_matrix, proj_matrix, do_color_management=True)
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

        print(max(image.pixels), min(image.pixels))

        # actually save image
        render_path = 'Z:\qa43nawu\\AB_render\\render.png'
        image.file_format = 'PNG'
        image.filepath_raw = render_path
        image.save()