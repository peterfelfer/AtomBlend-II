import bpy
import time

class AB_render:
    def render_frame(self, context, render_path=None):
        # set render path
        if render_path is not None:
            bpy.context.scene.render.filepath = render_path

        '''
        # set camera if it doesn't exist yet
        if bpy.context.scene.camera is None:
            bpy.ops.object.camera_add()

        # set matrices for rendering
        start = time.perf_counter()
        print('start', start)
        camera = bpy.context.scene.camera
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
        print('calc done', time.perf_counter() - start)
        '''
        # bpy.ops.render.render(animation=False, use_viewport=True, write_still=True)
        # print('render done', time.perf_counter() - start)