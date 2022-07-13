import bpy
import gpu
from gpu.types import GPUShader
from .shaders import *
# from .read_data import AtomBlendAddon
from .read_data import *
from gpu_extras.batch import batch_for_shader
from .globals import ABGlobals


class ABManagement:
    cache = {}

    @classmethod
    def init_shader(cls):
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
        if len(ABGlobals.atom_color_list) != len(ABGlobals.atom_coords):
            # print('ATOM COLOR LIST', ABGlobals.atom_color_list)
            # print('ATOM COORDS', ABGlobals.atom_coords)
            raise Exception("len atom cols != len atom coords", len(ABGlobals.atom_color_list), len(ABGlobals.atom_coords))
        batch = batch_for_shader(shader, 'POINTS', {'position': ABGlobals.atom_coords, 'color': ABGlobals.atom_color_list, })
        print('CLS', cls)

        # add draw handler that will be called every time this region in this space type will be drawn
        cls.handle = bpy.types.SpaceView3D.draw_handler_add(ABManagement.handler, (), 'WINDOW', 'POST_VIEW')

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

    @classmethod
    def handler(cls):
        # print('HANDLER')
        cls.render()

    @classmethod
    def render(cls):
        # print('RENDER')
        cache = ABManagement.cache
        shader = cache['shader']

        # bgl.glEnable(bgl.GL_PROGRAM_POINT_SIZE)
        # bgl.glEnable(bgl.GL_DEPTH_TEST)
        # bgl.glEnable(bgl.GL_BLEND)
        gpu.state.blend_set('ALPHA')
        gpu.state.program_point_size_set(True)
        gpu.state.depth_mask_set

        # uniform preparations
        projection_matrix = bpy.context.region_data.perspective_matrix

        object_matrix = bpy.data.objects['Empty'].matrix_world

        if len(ABGlobals.atom_coords) != len(ABGlobals.atom_color_list):
            print(len(ABGlobals.atom_coords), len(ABGlobals.atom_color_list))
            # print(ABGlobals.atom_coords, ABGlobals.atom_color_list)
            raise Exception("len atom cols != len atom coords", len(ABGlobals.atom_color_list), len(ABGlobals.atom_coords))

        cache['batch'] = batch_for_shader(shader, 'POINTS', {'position': ABGlobals.atom_coords, 'color': ABGlobals.atom_color_list, })

        # calculate matrices for rendering
        camera = cache['camera']
        render = bpy.context.scene.render
        view_matrix = camera.matrix_world.inverted()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        x = render.resolution_x
        y = render.resolution_y
        scale_x = render.pixel_aspect_x
        scale_y = render.pixel_aspect_y
        print('RENDER', x, y, scale_x, scale_y)
        camera_matrix = camera.calc_matrix_camera(depsgraph, x=x, y=y, scale_x=scale_x, scale_y=scale_y)
        projection_matrix = camera_matrix @ view_matrix  # matrix multiplication: camera_matrix * view_matrix
        print('CAMERA',camera_matrix)
        print('VIEW',view_matrix)
        print('PROJ',projection_matrix)
        # uniforms
        shader = cache['shader']
        shader.bind()
        shader.uniform_float('projection_matrix', projection_matrix)
        shader.uniform_float('object_matrix', object_matrix)
        shader.uniform_float('point_size', ABGlobals.point_size)
        shader.uniform_float('alpha_radius', 1.0)

        # draw
        batch = cache['batch']
        batch.draw(shader)
