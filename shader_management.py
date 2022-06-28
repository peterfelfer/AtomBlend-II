import bpy
import gpu
from gpu.types import GPUShader
from AtomBlend.shaders import *
# from AtomBlend.read_data import AtomBlendAddon
import AtomBlend.read_data
from gpu_extras.batch import batch_for_shader
from AtomBlend.globals import ABGlobals

class ABManagement:
    cache = {}

    @classmethod
    def init_shader(cls):
        # print('INIT')
        # init shader
        shader = GPUShader(ABShaders.vertex_shader_simple, ABShaders.fragment_shader_simple)

        # shader input
        # print('PRE FOR', ABGlobals.atom_color_list)
        ABGlobals.atom_color_list = []
        for elem_name in ABGlobals.all_elements_by_name:
            elem_amount = len(ABGlobals.all_elements_by_name[elem_name]['coordinates'])
            # print('elem amount vs len coordinates', elem_amount, len(ABGlobals.all_elements_by_name[elem_name]['coordinates']))

            col_struct = bpy.context.scene.color_settings[elem_name].color
            col = (col_struct[0], col_struct[1], col_struct[2], col_struct[3])
            print(col_struct, elem_name, elem_amount, col)
            # col = (col_struct[0], col_struct[1], col_struct[2], col_struct[3])
            ABGlobals.atom_color_list.append([col] * elem_amount)

        # print('ATOM COLOR LIST', elem_name, ABGlobals.atom_color_list)
            # print('ATOM COORDS', ABGlobals.atom_coords)

        # check if we have a list for each element for the atom coords and atom color list
        # -> flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        if isinstance(ABGlobals.atom_coords[0], list):
            ABGlobals.atom_coords = [x for xs in ABGlobals.atom_coords for x in xs] #https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

        print('PRE', ABGlobals.atom_color_list)
        if isinstance(ABGlobals.atom_color_list[0], list):
            ABGlobals.atom_color_list = [x for xs in ABGlobals.atom_color_list for x in xs]  # https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists
        print('POST', ABGlobals.atom_color_list)

        # print('atom color list vs atom coords', len(ABGlobals.atom_color_list), len(ABGlobals.atom_coords))

        if len(ABGlobals.atom_color_list) != len(ABGlobals.atom_coords):
            print('ATOM COLOR LIST', ABGlobals.atom_color_list)
            print('ATOM COORDS', ABGlobals.atom_coords)
            raise Exception("len atom cols != len atom coords", len(ABGlobals.atom_color_list), len(ABGlobals.atom_coords))
        batch = batch_for_shader(shader, 'POINTS', {'position': ABGlobals.atom_coords, 'color': ABGlobals.atom_color_list, })
        print('CLS', cls)

        # add draw handler that will be called every time this region in this space type will be drawn
        cls.handle = bpy.types.SpaceView3D.draw_handler_add(ABManagement.handler, (), 'WINDOW', 'POST_VIEW')

        # create empty object for object matrix
        bpy.ops.object.empty_add(type='PLAIN_AXES')

        # save in cache
        cache = ABManagement.cache
        cache['shader'] = shader
        cache['batch'] = batch

    @classmethod
    def handler(cls):
        # print('HANDLER')
        cls.render()

    @classmethod
    def render(cls):
        # print('RENDER')
        cache = ABManagement.cache
        shader = cache['shader']
        coords = ABGlobals.atom_coords

        # bgl.glEnable(bgl.GL_PROGRAM_POINT_SIZE)
        # bgl.glEnable(bgl.GL_DEPTH_TEST)
        # bgl.glEnable(bgl.GL_BLEND)
        gpu.state.blend_set('ALPHA')
        gpu.state.program_point_size_set(True)
        gpu.state.depth_mask_set

        # uniform preparations
        perspective_matrix = bpy.context.region_data.perspective_matrix

        object_matrix = bpy.data.objects['Empty'].matrix_world
        print(len(coords), len(ABGlobals.atom_color_list))
        print(coords, ABGlobals.atom_color_list)
        cache['batch'] = batch_for_shader(shader, 'POINTS', {'position': coords, 'color': ABGlobals.atom_color_list, })

        # uniforms
        shader = cache['shader']
        shader.bind()
        shader.uniform_float('perspective_matrix', perspective_matrix)
        shader.uniform_float('object_matrix', object_matrix)
        shader.uniform_float('point_size', ABGlobals.point_size)
        shader.uniform_float('alpha_radius', 1.0)
        # shader.uniform_float('global_alpha', 0.0)

        # draw
        batch = cache['batch']
        batch.draw(shader)
