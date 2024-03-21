import bpy
import bgl
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import *
from .shaders import *
from .read_data import *
from gpu_extras.batch import batch_for_shader
from .globals import ABGlobals
from gaussian_splatting import render


class DrawData:
    def __init__(self, ob):
        mesh = ob.data
        mat = ob.matrix_world

        diffuse_color = mesh.materials[0].diffuse_color
        verts = [mat @ v.co for v in mesh.vertices]
        ind = []

        for poly in mesh.polygons:
            ind.append([poly.vertices[i] for i in [0, 1, 2]])
            ind.append([poly.vertices[i] for i in [2, 3, 0]])

        self.color = diffuse_color
        self.verts = verts
        self.ind = ind

    def __del__(self):
        del self.color
        del self.verts
        del self.ind

    def draw(self):
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        shader.bind()
        shader.uniform_float("color", self.color)

        batch = batch_for_shader(shader, "TRIS", {"pos": self.verts}, indices=self.ind)
        batch.draw(shader)


class CustomRenderEngine(bpy.types.RenderEngine):
    # These three members are used by blender to set up the
    # RenderEngine; define its internal name, visible name and capabilities.
    bl_idname = "GAUSSIAN_SPLATTING_RENDERER"
    bl_label = "GSR"
    bl_use_preview = True

    # Init is called whenever a new render engine instance is created. Multiple
    # instances may exist at the same time, for example for a viewport and final
    # render.
    def __init__(self):
        self.scene_data = None
        print("RenderEngine created")

    # When the render engine instance is destroy, this is called. Clean up any
    # render engine data here, for example stopping running render threads.
    def __del__(self):
        del self.scene_data
        print("RenderEngine deleted")

    # This is the method called by Blender for both final renders (F12) and
    # small preview for materials, world and lights.
    def render(self, depsgraph):
        render.render_view_blender(ABGlobals.atom_coords)
        print('hi')

    # For viewport renders, this method gets called once at the start and
    # whenever the scene or 3D viewport changes. This method is where data
    # should be read from Blender in the same thread. Typically a render
    # thread will be started to do the work while keeping Blender responsive.
    def view_update(self, context, depsgraph):

        region = context.region
        view3d = context.space_data
        scene = depsgraph.scene

        # Get viewport dimensions
        dimensions = region.width, region.height

        if not self.scene_data:
            # First time initialization
            self.scene_data = {}  # Dictionary
            first_time = True

            # Loop over all datablocks used in the scene.
            for datablock in depsgraph.ids:
                pass
        else:
            first_time = False

            # Test which datablocks changed
            for update in depsgraph.updates:
                print("Datablock updated: ", update.id.name)

            # Test if any material was added, removed or changed.
            if depsgraph.id_type_updated('MATERIAL'):
                print("Materials updated")

        # Loop over all object instances in the scene.
        if first_time or depsgraph.id_type_updated('OBJECT'):
            for instance in depsgraph.object_instances:
                ob = instance.object
                if ob.type == 'MESH':
                    print("\tname: %s \ttype: %s" % (ob.name, ob.type))

                    self.scene_data[ob.name] = DrawData(ob)

    # For viewport renders, this method is called whenever Blender redraws
    # the 3D viewport. The renderer is expected to quickly draw the render
    # with OpenGL, and not perform other expensive work.
    # Blender will draw overlays for selection and editing on top of the
    # rendered image automatically.
    def view_draw(self, context, depsgraph):

        view3d = context.space_data
        r3d = view3d.region_3d

        gpu.matrix.load_matrix(r3d.perspective_matrix)
        gpu.matrix.load_projection_matrix(Matrix.Identity(4))

        gpu.state.depth_test_set('ALWAYS')
        gpu.state.depth_mask_set(True)

        # bgl.glClearColor(0.01, 0.01, 0.01, 1)
        # bgl.glClear(bgl.GL_COLOR_BUFFER_BIT | bgl.GL_DEPTH_BUFFER_BIT)
        # bgl.glEnable(bgl.GL_DEPTH_TEST)

        cache = ABManagement.cache
        shader = cache['shader']

        if len(ABGlobals.atom_color_list) != len(ABGlobals.atom_coords):
            raise Exception("len atom cols != len atom coords", len(ABGlobals.atom_color_list), len(ABGlobals.atom_coords))

        if (len(ABGlobals.atom_coords) != len(ABGlobals.atom_color_list)) or (
                len(ABGlobals.atom_coords) != len(ABGlobals.point_size_list)) or (
                len(ABGlobals.atom_color_list) != len(ABGlobals.point_size_list)):
            print(len(ABGlobals.atom_coords), len(ABGlobals.atom_color_list), len(ABGlobals.point_size_list))

        l = len(ABGlobals.atom_color_list)
        ABGlobals.atom_color_list = []
        col = (1, 0, 0, 1)
        ABGlobals.atom_color_list.append([col] * l)
        ABGlobals.atom_color_list = ABGlobals.atom_color_list[0]

        batch = batch_for_shader(shader, 'POINTS', {'position': ABGlobals.atom_coords, 'color': ABGlobals.atom_color_list, 'ps': ABGlobals.point_size_list})

        # uniform preparations
        proj_matrix = bpy.context.region_data.perspective_matrix
        object_matrix = bpy.data.objects['Top'].matrix_world

        # pass uniforms to shader
        shader.bind()
        shader.uniform_float('projection_matrix', proj_matrix)
        shader.uniform_float('object_matrix', object_matrix)
        batch.draw(shader)

        for ob_name in self.scene_data:
            drawdata = self.scene_data[ob_name]

            drawdata.draw()

        gpu.state.depth_mask_set(False)