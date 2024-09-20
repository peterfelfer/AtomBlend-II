import glfw
import OpenGL.GL as gl
from imgui.integrations.glfw import GlfwRenderer
import imgui
import numpy as np
import util
import imageio
import util_gau
import tkinter as tk
from tkinter import filedialog
import os
import sys
import argparse
import torch
from renderer_ogl import OpenGLRenderer, GaussianRenderBase
import threading
import dpg_plotting
import dearpygui.dearpygui as dpg

# Add the directory containing main.py to the Python path
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)

# Change the current working directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))


g_camera = util.Camera(720, 1280)
BACKEND_OGL=0
BACKEND_CUDA=1
g_renderer_list = [
    None, # ogl
]
g_renderer_idx = BACKEND_OGL
g_renderer: GaussianRenderBase = g_renderer_list[g_renderer_idx]
g_scale_modifier = 1.
g_auto_sort = False
g_show_control_win = True
g_show_help_win = False
g_show_camera_win = True
g_show_atom_settings_win = True
g_show_debug_win = True
g_render_mode_tables_ogl = ["Gaussian Ball", "Flat Ball", "Billboard", "Depth", "SH:0", "SH:0~1", "SH:0~2", "SH:0~3"]
g_render_mode_tables_cuda = ["Phong Shading", "Flat", "Gaussian Splatting", "Gaussian Ball", "Gaussian Ball Opt"]
g_render_mode = 3
g_render_cov3D = True

global_alpha = 1.0
global_scale = 0.1
render_all_elements = True
file_path = ''

debug_covmat = np.asarray([1.0, 0.0, 0.0, 1.0, 0.0, 1.0])
volume_opacity = False
individual_opacity_state = 2

def impl_glfw_init():
    window_name = "Interactive Gaussian Splatting Atom Probe Set Viewer"

    if not glfw.init():
        print("Could not initialize OpenGL context")
        exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    # glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    # Create a windowed mode window and its OpenGL context
    global window
    window = glfw.create_window(
        g_camera.w, g_camera.h, window_name, None, None
    )
    glfw.maximize_window(window)
    glfw.make_context_current(window)
    glfw.swap_interval(0)
    # glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL);
    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        exit(1)

    return window

def cursor_pos_callback(window, xpos, ypos):
    if imgui.get_io().want_capture_mouse:
        g_camera.is_leftmouse_pressed = False
        g_camera.is_rightmouse_pressed = False
    g_camera.process_mouse(xpos, ypos)

def mouse_button_callback(window, button, action, mod):
    if imgui.get_io().want_capture_mouse:
        return
    pressed = action == glfw.PRESS
    g_camera.is_leftmouse_pressed = (button == glfw.MOUSE_BUTTON_LEFT and pressed)
    g_camera.is_rightmouse_pressed = (button == glfw.MOUSE_BUTTON_RIGHT and pressed)

def wheel_callback(window, dx, dy):
    g_camera.process_wheel(dx, dy)

def key_callback(window, key, scancode, action, mods):
    if action == glfw.REPEAT or action == glfw.PRESS:
        if key == glfw.KEY_Q:
            g_camera.process_roll_key(1)
        elif key == glfw.KEY_E:
            g_camera.process_roll_key(-1)
        elif key == glfw.KEY_W:
            g_camera.process_move_key(0, 1, 0)
        elif key == glfw.KEY_S:
            g_camera.process_move_key(0, -1, 0)
        elif key == glfw.KEY_A:
            g_camera.process_move_key(1, 0, 0)
        elif key == glfw.KEY_D:
            g_camera.process_move_key(-1, 0, 0)
        elif key == glfw.KEY_R:
            g_camera.process_move_key(0, 0, 1)
        elif key == glfw.KEY_F:
            g_camera.process_move_key(0, 0, -1)
        elif key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(window, True)

def update_camera_pose_lazy():
    if g_camera.is_pose_dirty:
        g_renderer.update_camera_pose(g_camera)
        g_camera.is_pose_dirty = False

def update_camera_intrin_lazy():
    if g_camera.is_intrin_dirty:
        g_renderer.update_camera_intrin(g_camera)
        g_camera.is_intrin_dirty = False

def update_activated_renderer_state(gaus: util_gau.GaussianData):
    g_renderer.update_gaussian_data(gaus)
    g_renderer.sort_and_update(g_camera)
    g_renderer.set_scale_modifier(g_scale_modifier)
    if g_renderer_idx == 0:  # ogl
        g_renderer.set_render_mod(g_render_mode - 3)
    else:  # cuda
        g_renderer.set_render_mod(g_render_mode)
    g_renderer.update_camera_pose(g_camera)
    g_renderer.update_camera_intrin(g_camera)
    g_renderer.set_render_reso(g_camera.w, g_camera.h)

    # set_individual_opacity(gaus)

def window_resize_callback(window, width, height):
    gl.glViewport(0, 0, width, height)
    g_camera.update_resolution(height, width)
    g_renderer.set_render_reso(width, height)


def changed_render_all_elements(gaussians):
    for elem in gaussians.num_of_atoms_by_element:
        col = gaussians.num_of_atoms_by_element[elem]['color']
        if render_all_elements:
            gaussians.num_of_atoms_by_element[elem]['is_rendered'] = True
            gaussians.num_of_atoms_by_element[elem]['color'] = (col[0], col[1], col[2], 1.0)
        else:
            gaussians.num_of_atoms_by_element[elem]['is_rendered'] = False
            gaussians.num_of_atoms_by_element[elem]['color'] = (col[0], col[1], col[2], 0.0)

    set_index_properties(gaussians)

def set_index_properties(gaussians):
    index_properties = []
    for elem in gaussians.num_of_atoms_by_element:
        col = gaussians.num_of_atoms_by_element[elem]['color']
        scale = gaussians.num_of_atoms_by_element[elem]['scale']
        index_properties.extend([col[0], col[1], col[2], col[3], scale])

    g_renderer.raster_settings["index_properties"] = torch.Tensor(index_properties).float().cuda()

    g_renderer.update_gaussian_data(gaussians)
    g_renderer.sort_and_update(g_camera)

def set_cov3D_changes(gaussians):
    if not g_render_cov3D:
        g_renderer.set_scale_modifier(0.1)
    else:
        g_renderer.set_scale_modifier(20.0)

    g_renderer.update_gaussian_data(gaussians)
    g_renderer.sort_and_update(g_camera)

def set_color(gaussians, elem):
    col = gaussians.num_of_atoms_by_element[elem]['color']

    if gaussians.num_of_atoms_by_element[elem]['is_rendered']:
        gaussians.num_of_atoms_by_element[elem]['color'] = (col[0], col[1], col[2], 1.0)
    else:
        gaussians.num_of_atoms_by_element[elem]['color'] = (col[0], col[1], col[2], 0.0)

    set_index_properties(gaussians)

def set_global_alpha(gaussians, alpha):
    for elem in gaussians.num_of_atoms_by_element:
        col = gaussians.num_of_atoms_by_element[elem]['color']

        if gaussians.num_of_atoms_by_element[elem]['is_rendered']:
            gaussians.num_of_atoms_by_element[elem]['color'] = (col[0], col[1], col[2], alpha)

    set_index_properties(gaussians)

def set_global_scale(gaussians, scale):
    for elem in gaussians.num_of_atoms_by_element:
        gaussians.num_of_atoms_by_element[elem]['scale'] = scale

    set_index_properties(gaussians)

def main():
    global g_camera, g_renderer, g_renderer_list, g_renderer_idx, g_scale_modifier, g_auto_sort, \
        g_show_control_win, g_show_help_win, g_show_camera_win, g_show_debug_win, \
        g_render_mode, g_render_mode_tables_ogl, g_render_mode_tables_cuda, global_scale, global_alpha, \
        g_render_cov3D, debug_covmat, render_all_elements, file_path, volume_opacity, \
        individual_opacity_state
        
    imgui.create_context()
    if args.hidpi:
        imgui.get_io().font_global_scale = 1.5
    window = impl_glfw_init()
    impl = GlfwRenderer(window)
    root = tk.Tk()  # used for file dialog
    root.withdraw()
    
    glfw.set_cursor_pos_callback(window, cursor_pos_callback)
    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_scroll_callback(window, wheel_callback)
    glfw.set_key_callback(window, key_callback)
    
    glfw.set_window_size_callback(window, window_resize_callback)

    # init renderer
    g_renderer_list[BACKEND_OGL] = OpenGLRenderer(g_camera.w, g_camera.h)
    try:
        from renderer_cuda import CUDARenderer
        g_renderer_list += [CUDARenderer(g_camera.w, g_camera.h)]
    except ImportError:
        g_renderer_idx = BACKEND_OGL
    else:
        g_renderer_idx = BACKEND_CUDA

    g_renderer = g_renderer_list[g_renderer_idx]

    # gaussian data; naive gaussian
    # gaussians = util_gau.naive_gaussian()

    # load "dummy" ply
    gaussians = util_gau.load_ply('/home/qa43nawu/temp/qa43nawu/out/test.ply')
    update_activated_renderer_state(gaussians)
    set_index_properties(gaussians)

    # settings
    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        imgui.new_frame()

        gl.glClearColor(0, 0, 0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        update_camera_pose_lazy()
        update_camera_intrin_lazy()

        g_renderer.draw(g_render_cov3D, individual_opacity_state)

        if g_show_atom_settings_win:
            imgui.core.set_next_window_position(0, 0, imgui.ONCE)
            imgui.core.set_next_window_size(720, 1200, imgui.ONCE)
            if imgui.begin("Atom Settings", True):
                imgui.core.set_window_font_scale(2.0)

                imgui.text('Display settings:')

                imgui.core.push_item_width(500)
                changed, global_alpha = imgui.core.drag_float('Global alpha', global_alpha, 0.01, 0.0, 1.0)
                if changed:
                    set_global_alpha(gaussians, global_alpha)
                changed, global_scale = imgui.core.drag_float('Global scale', global_scale, 0.01, 0.0, 10.0)
                if changed:
                    set_global_scale(gaussians, global_scale)

                imgui.text('Element settings:')

                changed, render_all_elements = imgui.core.checkbox('', render_all_elements)
                if changed:
                    changed_render_all_elements(gaussians)

                imgui.same_line()
                imgui.text('Name')

                imgui.same_line(80, 50)
                imgui.text('#Atoms')

                imgui.same_line(200, 50)
                imgui.text('Color (R, G, B, A)')

                imgui.same_line(580)
                imgui.text('Scale')

                for elem in gaussians.num_of_atoms_by_element:
                    imgui.push_id(elem)

                    changed, gaussians.num_of_atoms_by_element[elem]['is_rendered'] = imgui.core.checkbox('##' + elem, gaussians.num_of_atoms_by_element[elem]['is_rendered'])

                    if changed:
                        set_color(gaussians, elem)

                    imgui.same_line()

                    imgui.text(elem)
                    imgui.same_line(80, 50)

                    imgui.text(str(gaussians.num_of_atoms_by_element[elem]['num']))
                    imgui.same_line(200, 50)

                    imgui.core.push_item_width(300)

                    # imgui.table_set_column_index(1)
                    changed, gaussians.num_of_atoms_by_element[elem]['color'] = imgui.core.color_edit4('##slider_scale' + elem, *gaussians.num_of_atoms_by_element[elem]['color'])

                    if changed:
                        set_index_properties(gaussians)

                    # imgui.table_set_column_index(2)
                    imgui.same_line(spacing=25)

                    imgui.core.push_item_width(100)

                    changed, gaussians.num_of_atoms_by_element[elem]['scale'] = imgui.core.drag_float('', gaussians.num_of_atoms_by_element[elem]['scale'], 0.01, 0.0, 10.0)

                    if changed:
                        set_index_properties(gaussians)

                    imgui.pop_id()

            imgui.end()

        if g_show_control_win:
            imgui.core.set_next_window_position(0, 1200, imgui.ONCE)
            imgui.core.set_next_window_size(720, 1200, imgui.ONCE)
            if imgui.begin("Control", True):
                imgui.core.set_window_font_scale(2.0)

                if imgui.tree_node("Load file", imgui.TREE_NODE_FRAMED):
                    if imgui.button(label='open test.ply'):
                        # file_path = '/home/qa43nawu/temp/qa43nawu/out/point_cloud_cov_normalized.ply'
                        file_path = '/home/qa43nawu/temp/qa43nawu/out/test.ply'

                        if file_path:
                            try:
                                gaussians = util_gau.load_ply(file_path)
                                set_index_properties(gaussians)
                                g_renderer.update_gaussian_data(gaussians)
                                g_renderer.sort_and_update(g_camera)
                            except RuntimeError as e:
                                pass

                    if imgui.button(label='open .ply'):
                        file_path = filedialog.askopenfilename(title="open ply",
                                                               initialdir="/home/qa43nawu/temp/qa43nawu/out/",
                                                               filetypes=[('ply file', '.ply')]
                                                               )
                        if file_path:
                            try:
                                gaussians = util_gau.load_ply(file_path)
                                set_index_properties(gaussians)
                                g_renderer.update_gaussian_data(gaussians)
                                g_renderer.sort_and_update(g_camera)
                            except RuntimeError as e:
                                pass

                    imgui.text("Loaded file: " + file_path.split('/')[-1])
                    imgui.text(f"Number of Atoms = {len(gaussians)}")
                    imgui.tree_pop()

                imgui.spacing()
                imgui.separator()
                imgui.spacing()

                if imgui.tree_node("Individual opacity", imgui.TREE_NODE_FRAMED | imgui.TREE_NODE_DEFAULT_OPEN):
                    changed = imgui.radio_button("Depending on volume", individual_opacity_state == 0)
                    if changed:
                        individual_opacity_state = 0
                        g_renderer.sort_and_update(g_camera)
                    changed = imgui.radio_button("Depending on distance to neighbors", individual_opacity_state == 1)
                    if changed:
                        individual_opacity_state = 1
                        g_renderer.sort_and_update(g_camera)
                    changed = imgui.radio_button("No individual opacity", individual_opacity_state == 2)
                    if changed:
                        individual_opacity_state = 2
                        g_renderer.sort_and_update(g_camera)

                    changed, new = imgui.core.drag_float("Intensity", g_renderer.raster_settings["individual_opacity_factor"], 0.01, -1.0, 1.0)
                    if changed:
                        g_renderer.raster_settings["individual_opacity_factor"] = new
                        g_renderer.sort_and_update(g_camera)

                    if imgui.tree_node("Advanced settings", imgui.TREE_NODE_FRAMED | imgui.TREE_NODE_DEFAULT_OPEN):

                        if imgui.button("Show distance plot", 100, 100):
                            glfw.make_context_current(None)
                            dpg_plotting.open_plotting_window(gaussians, g_renderer)

                            # thread = threading.Thread(target=dpg_plotting.open_plotting_window(gaussians, g_renderer))
                            # thread.start()

                            glfw.make_context_current(window)

                        imgui.tree_pop()
                    imgui.tree_pop()

                imgui.spacing()
                imgui.separator()
                imgui.spacing()

                if imgui.tree_node("Camera settings", imgui.TREE_NODE_FRAMED):

                    # if imgui.button(label='rot 180'):
                    #     g_camera.flip_ground()

                    # changed, g_camera.target_dist = imgui.drag_float(
                    #     "t", g_camera.target_dist, 0.1, 1., 8., "target dist = %.3f"
                    # )
                    # if changed:
                    #     g_camera.update_target_distance()

                    imgui.push_id("0")
                    changed, g_camera.rot_sensitivity = imgui.drag_float(
                        "##r", g_camera.rot_sensitivity, 0.01, 0.001, 1.0, "rotate speed = %.3f"
                    )
                    imgui.same_line()
                    if imgui.button(label="reset"):
                        g_camera.rot_sensitivity = 0.5
                    imgui.pop_id()

                    imgui.push_id("1")
                    changed, g_camera.trans_sensitivity = imgui.drag_float(
                        "##m", g_camera.trans_sensitivity, 0.01, 0.001, 1.0, "move speed = %.3f"
                    )
                    imgui.same_line()
                    if imgui.button(label="reset"):
                        g_camera.trans_sensitivity = 0.5
                    imgui.pop_id()

                    imgui.push_id("2")
                    changed, g_camera.zoom_sensitivity = imgui.drag_float(
                        "##z", g_camera.zoom_sensitivity, 0.01, 0.01, 1.0, "zoom speed = %.3f"
                    )
                    imgui.same_line()
                    if imgui.button(label="reset"):
                        g_camera.zoom_sensitivity = 0.5
                    imgui.pop_id()

                    imgui.push_id("3")
                    changed, g_camera.roll_sensitivity = imgui.drag_float(
                        "##ro", g_camera.roll_sensitivity, 0.01, 0.01, 1.0, "roll speed = %.3f"
                    )
                    imgui.same_line()
                    if imgui.button(label="reset"):
                        g_camera.roll_sensitivity = 0.03
                    imgui.pop_id()

                    changed, g_camera.fovy = imgui.core.drag_float("Field of view", g_camera.fovy, 0.01, 0.001, 100)

                    if changed:
                        g_camera.is_pose_dirty = True

                    imgui.tree_pop()

                imgui.spacing()
                imgui.separator()
                imgui.spacing()

                if imgui.tree_node("Rendering", imgui.TREE_NODE_FRAMED):

                    #### render mode ####
                    if g_renderer_idx == 0:  # ogl
                        changed, g_render_mode = imgui.combo("shading", g_render_mode, g_render_mode_tables_ogl)
                    else:  # cuda
                        changed, g_render_mode = imgui.combo("shading", g_render_mode, g_render_mode_tables_cuda)

                    if changed:
                        if g_renderer_idx == 0:  # ogl
                            g_renderer.set_render_mod(g_render_mode - 4)
                        else:  # cuda
                            g_renderer.set_render_mod(g_render_mode)

                    #### cov3d ####
                    changed, g_render_cov3D = imgui.core.checkbox('Shape atoms (use covariance matrices)', g_render_cov3D)
                    if changed:
                        set_cov3D_changes(gaussians)

                    imgui.tree_pop()

                imgui.spacing()
                imgui.separator()
                imgui.spacing()

                if imgui.tree_node("Save image", imgui.TREE_NODE_FRAMED):
                    if imgui.button(label='save image'):
                        width, height = glfw.get_framebuffer_size(window)
                        nrChannels = 3;
                        stride = nrChannels * width;
                        stride += (4 - stride % 4) if stride % 4 else 0
                        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT, 4)
                        gl.glReadBuffer(gl.GL_FRONT)
                        bufferdata = gl.glReadPixels(0, 0, width, height, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
                        img = np.frombuffer(bufferdata, np.uint8, -1).reshape(height, width, 3)
                        imageio.imwrite("/home/qa43nawu/temp/qa43nawu/out/viewer/save.png", img[::-1])
                        # save intermediate information
                        # np.savez(
                        #     "save.npz",
                        #     gau_xyz=gaussians.xyz,
                        #     gau_s=gaussians.scale,
                        #     gau_rot=gaussians.rot,
                        #     gau_c=gaussians.sh,
                        #     gau_a=gaussians.opacity,
                        #     viewmat=g_camera.get_view_matrix(),
                        #     projmat=g_camera.get_project_matrix(),
                        #     hfovxyfocal=g_camera.get_htanfovxy_focal()
                        # )

                        ########################
                        # matrix = [[0.0 for _ in range(3)] for _ in range(3)]
                    imgui.tree_pop()

                imgui.spacing()
                imgui.separator()
                imgui.spacing()

                imgui.text(f"fps = {imgui.get_io().framerate:.1f}")
                changed, g_renderer.reduce_updates = imgui.checkbox(
                    "reduce updates", g_renderer.reduce_updates,
                )
                _, g_show_debug_win = imgui.checkbox("Show debug window", g_show_debug_win)
                _, g_show_help_win = imgui.checkbox("Show help window", g_show_help_win)

                imgui.end()


        if g_show_camera_win:
            pass

        if g_show_help_win:
            imgui.core.set_next_window_position(720, 0, imgui.ONCE)
            imgui.core.set_next_window_size(720, 430, imgui.ONCE)
            imgui.begin("Help", True)
            imgui.core.set_window_font_scale(2.0)
            imgui.text("Open a preprocessed .ply file by clicking \n 'open .ply' in Control > Load file.")

            imgui.text('')
            imgui.text("Control:")
            imgui.text("WASD or right mouse button: Move the camera")
            imgui.text("Left mouse button: Rotate the camera")
            imgui.text("Q/E: Roll camera")
            imgui.text("Mouse wheel scrolling: Zoom in or out")

            imgui.text('')
            imgui.text('Click and hold on a slider to change its \n setting. You can also double click on the \n slider to enter a custom number that \n also can be off the bounds.')

            # imgui.begin("Help", True)

            # imgui.text("Open Gaussian Splatting PLY file \n  by clicking 'open .ply' button")
            # imgui.text("Use left click & move to rotate camera")
            # imgui.text("Use right click & move to translate camera")
            # imgui.text("Press Q/E to roll camera")
            # imgui.text("Use scroll to zoom in/out")
            # imgui.text("Use control panel to change setting")
            imgui.end()


        if g_show_debug_win:
            if imgui.begin("Debug", True):
                imgui.core.set_window_font_scale(2.0)

                #### rendering backend ####
                changed, g_renderer_idx = imgui.combo("backend", g_renderer_idx, ["ogl", "cuda"][:len(g_renderer_list)])
                if changed:
                    g_renderer = g_renderer_list[g_renderer_idx]
                    update_activated_renderer_state(gaussians)

                #### covmat ####
                imgui.text('Debug CovMat:')
                if imgui.begin_table("matrix_table", 3):
                    # Fill the table with matrix data
                    # for row in range(3):
                    #     imgui.table_next_row()
                    #     for col in range(3):
                    #         imgui.table_set_column_index(col)
                            # changed, debug_covmat[row][col] = imgui.slider_float(f"##cell{row}{col}", debug_covmat[row][col], -1, 1, format="%.3f")

                    c1, c2, c3, c4, c5, c6 = False, False, False, False, False, False

                    imgui.table_next_row()

                    imgui.table_set_column_index(0)
                    c1, debug_covmat[0] = imgui.drag_float(f"##cell{0}{0}", debug_covmat[0], 0.01, -1, 1, format="%.3f")
                    imgui.table_set_column_index(1)
                    c2, debug_covmat[1] = imgui.drag_float(f"##cell{0}{1}", debug_covmat[1], 0.01, -1, 1, format="%.3f")
                    imgui.table_set_column_index(2)
                    c3, debug_covmat[2] = imgui.drag_float(f"##cell{0}{2}", debug_covmat[2], 0.01, -1, 1, format="%.3f")

                    imgui.table_next_row()
                    imgui.table_set_column_index(1)
                    c4, debug_covmat[3] = imgui.drag_float(f"##cell{1}{1}", debug_covmat[3], 0.01, -1, 1, format="%.3f")
                    imgui.table_set_column_index(2)
                    c5, debug_covmat[4] = imgui.drag_float(f"##cell{1}{2}", debug_covmat[4], 0.01, -1, 1, format="%.3f")

                    imgui.table_next_row()
                    imgui.table_set_column_index(2)
                    c6, debug_covmat[5] = imgui.drag_float(f"##cell{2}{2}", debug_covmat[5], 0.01, -1, 1, format="%.3f")

                    if c1 or c2 or c3 or c4 or c5 or c6:
                        gaussians.cov3D = np.tile(debug_covmat, (gaussians.opacity.shape[0], 1))
                        g_renderer.update_gaussian_data(gaussians)

                        # print(gaussians.cov3D)

                    imgui.end_table()

                    #### sort button ####
                    if imgui.button(label='sort Gaussians'):
                        g_renderer.sort_and_update(g_camera)
                    imgui.same_line()
                    changed, g_auto_sort = imgui.checkbox(
                        "auto sort", g_auto_sort,
                    )
                    if g_auto_sort:
                        g_renderer.sort_and_update(g_camera)

                    #
                    changed, g_camera.right = imgui.drag_float('right', g_camera.right, 1, 0, 5000)
                    if changed:
                        g_renderer.sort_and_update(g_camera)
                        g_camera.is_pose_dirty = True

                    changed, g_camera.top = imgui.drag_float('top', g_camera.top, 1, 0, 5000)
                    if changed:
                        g_renderer.sort_and_update(g_camera)
                        g_camera.is_pose_dirty = True


                    imgui.spacing()
                    imgui.separator()
                    imgui.spacing()

                    # camera debug settings
                    changed, new = imgui.drag_float3('camera position', g_camera.position[0], g_camera.position[1], g_camera.position[2], 0.1, )
                    if changed:
                        g_camera.position[0] = new[0]
                        g_camera.position[1] = new[1]
                        g_camera.position[2] = new[2]
                        g_renderer.sort_and_update(g_camera)
                        g_camera.is_pose_dirty = True

                    changed, new = imgui.drag_float3('camera target', g_camera.target[0], g_camera.target[1], g_camera.target[2], 0.1, )
                    if changed:
                        g_camera.target[0] = new[0]
                        g_camera.target[1] = new[1]
                        g_camera.target[2] = new[2]
                        g_renderer.sort_and_update(g_camera)
                        g_camera.is_pose_dirty = True

                    changed, new = imgui.drag_float3('camera up', g_camera.up[0], g_camera.up[1],
                                                     g_camera.up[2], 0.1, )
                    if changed:
                        g_camera.up[0] = new[0]
                        g_camera.up[1] = new[1]
                        g_camera.up[2] = new[2]
                        g_renderer.sort_and_update(g_camera)
                        g_camera.is_pose_dirty = True


            imgui.end()

        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    global args
    parser = argparse.ArgumentParser(description="NeUVF editor with optional HiDPI support.")
    parser.add_argument("--hidpi", action="store_true", help="Enable HiDPI scaling for the interface.")
    args = parser.parse_args()

    main()
