import bpy
import bgl
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
        coords = ABGlobals.atom_coords
        element_count = ABGlobals.element_count

        for elem_name in element_count:
            elem_amount = element_count[elem_name]

            col_struct = bpy.context.scene.color_settings[elem_name].color
            col = (col_struct[0], col_struct[1], col_struct[2], col_struct[3])
            # col = (col_struct[0], col_struct[1], col_struct[2], col_struct[3])
            ABGlobals.atom_color_list.append([col] * elem_amount)

        # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
        ABGlobals.atom_color_list = [x for xs in ABGlobals.atom_color_list for x in xs] #https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

        # print(ABGlobals.atom_color_list)
        print('LENGTH', len(ABGlobals.atom_color_list), len(coords))

        batch = batch_for_shader(shader, 'POINTS', {'position': coords, 'color': ABGlobals.atom_color_list, })
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

        bgl.glEnable(bgl.GL_PROGRAM_POINT_SIZE)
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glEnable(bgl.GL_BLEND)

        # uniform preparations
        perspective_matrix = bpy.context.region_data.perspective_matrix


        # object_matrix = bpy.data.objects['Plane'].matrix_world # TODO change to empty object that is created in this function

        object_matrix = bpy.data.objects['Empty'].matrix_world
        cache['batch'] = batch_for_shader(shader, 'POINTS', {'position': coords, 'color': ABGlobals.atom_color_list, })

        # uniforms
        shader = cache['shader']
        shader.bind()
        shader.uniform_float('perspective_matrix', perspective_matrix)
        shader.uniform_float('object_matrix', object_matrix)
        shader.uniform_float('point_size', 5.0)
        shader.uniform_float('alpha_radius', 1.0)
        # shader.uniform_float('global_alpha', 0.0)

        # draw
        batch = cache['batch']
        batch.draw(shader)
