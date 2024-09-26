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
import dearpygui.dearpygui as dpg

# Add the directory containing main.py to the Python path
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)

# Change the current working directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

g_camera = util.Camera(720, 1280)
BACKEND_OGL = 0
BACKEND_CUDA = 1
g_renderer_list = [
    None,  # ogl
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
g_volume = False
individual_opacity_state = 2


def dearpygui_init():
    dpg.create_context()


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
        g_render_cov3D, debug_covmat, render_all_elements, file_path, g_volume, \
        individual_opacity_state

    imgui.create_context()

    dpg.create_context()
    # with dpg.window(label="DearPyGui Window"):
    #     dpg.add_button(label="Click Me")

    if args.hidpi:
        imgui.get_io().font_global_scale = 1.5

    dpg.create_context()
    dpg.create_viewport(title="bla", width=800, height=600)
    dpg.setup_dearpygui()
    with dpg.window(label="Example Window"):
        dpg.add_text("Hello, world")

    dpg.show_viewport()


    root = tk.Tk()  # used for file dialog
    root.withdraw()

    # glfw.set_cursor_pos_callback(window, cursor_pos_callback)
    # glfw.set_mouse_button_callback(window, mouse_button_callback)
    # glfw.set_scroll_callback(window, wheel_callback)
    # glfw.set_key_callback(window, key_callback)
    #
    # glfw.set_window_size_callback(window, window_resize_callback)

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

    texture_data = []
    for i in range(0, 1280 * 720):
        texture_data.append(255 / 255)
        texture_data.append(0)
        texture_data.append(255 / 255)
        texture_data.append(255 / 255)

    with dpg.texture_registry():
        dpg.add_raw_texture(1280, 720, default_value=texture_data, tag="3d_scene_texture")

    # settings
    # while not glfw.window_should_close(window):
    while dpg.is_dearpygui_running():
        # glfw.poll_events()
        # impl.process_inputs()
        # imgui.new_frame()

        gl.glClearColor(0, 0, 0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        update_camera_pose_lazy()
        update_camera_intrin_lazy()

        texture_data = g_renderer.draw(g_render_cov3D, individual_opacity_state)

        # Register the texture in DearPyGui


        # Show the texture in a DearPyGui window
        with dpg.window(label="3D Scene"):
            dpg.add_image("3d_scene_texture")

        ## IMGUI

        dpg.render_dearpygui_frame()
        dpg.set_value("3d_scene_texture", texture_data)

        # imgui.render()
        # impl.render(imgui.get_draw_data())
        # glfw.swap_buffers(window)

    # impl.shutdown()
    dpg.destroy_context()
    glfw.terminate()


if __name__ == "__main__":
    global args
    parser = argparse.ArgumentParser(description="NeUVF editor with optional HiDPI support.")
    parser.add_argument("--hidpi", action="store_true", help="Enable HiDPI scaling for the interface.")
    args = parser.parse_args()

    main()
