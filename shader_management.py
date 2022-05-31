import bpy
import bgl
from gpu.types import GPUShader
from AtomBlend.shaders import *
from gpu_extras.batch import batch_for_shader


class ABManagement:
    cache = {}

    @classmethod
    def init_shader(cls, coords):
        print('INIT')
        # init shader
        shader = GPUShader(ABShaders.vertex_shader_simple, ABShaders.fragment_shader_simple)
        # shader input
        color_list = [(1.0, 0.0, 0.0, 1.0)] * len(coords)
        batch = batch_for_shader(shader, 'POINTS', {'position': coords, 'color': color_list, })
        print('CLS', cls)
        # add draw handler that will called every time this region in this space type will be drawn
        cls.handle = bpy.types.SpaceView3D.draw_handler_add(ABManagement.handler, (), 'WINDOW', 'POST_VIEW')

        # save in cache
        cache = ABManagement.cache
        cache['shader'] = shader
        cache['batch'] = batch

    @classmethod
    def handler(cls):
        print('HANDLER')
        cls.render()

    @classmethod
    def render(cls):
        print('RENDER')
        cache = ABManagement.cache

        bgl.glEnable(bgl.GL_PROGRAM_POINT_SIZE)
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glEnable(bgl.GL_BLEND)
        # uniform preparations
        perspective_matrix = bpy.context.region_data.perspective_matrix
        object_matrix = bpy.data.objects['Plane'].matrix_world # TODO correct object like Atoms or something

        # uniforms
        shader = cache['shader']
        shader.bind()
        shader.uniform_float('perspective_matrix', perspective_matrix)
        shader.uniform_float('object_matrix', object_matrix)
        shader.uniform_float('point_size', 5.0)
        shader.uniform_float('alpha_radius', 1000.0)
        shader.uniform_float('global_alpha', 1.0)

        # draw
        batch = cache['batch']
        batch.draw(shader)
