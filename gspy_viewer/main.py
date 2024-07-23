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
g_render_mode_tables_ogl = ["Gaussian Ball", "Flat Ball", "Billboard", "Depth", "SH:0", "SH:0~1", "SH:0~2", "SH:0~3"]
g_render_mode_tables_cuda = ["Phong Shading", "Flat", "Gaussian Splatting", "Gaussian Ball", "Gaussian Ball Opt"]
g_render_mode = 4
g_render_cov3D = True

global_alpha = 1.0
global_scale = 1.0
render_all_elements = True

debug_covmat = np.asarray([1.0, 0.0, 0.0, 1.0, 0.0, 1.0])




def impl_glfw_init():
    window_name = "NeUVF editor"

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

def window_resize_callback(window, width, height):
    gl.glViewport(0, 0, width, height)
    g_camera.update_resolution(height, width)
    g_renderer.set_render_reso(width, height)


def changed_render_all_elements(gaussians):
    for key in gaussians.num_of_atoms_by_element:
        if render_all_elements:
            gaussians.num_of_atoms_by_element[key]['is_rendered'] = True
        else:
            gaussians.num_of_atoms_by_element[key]['is_rendered'] = False

    set_colors(gaussians)
    g_renderer.update_gaussian_data(gaussians)
    g_renderer.sort_and_update(g_camera)


def set_colors(gaussians, global_alpha=None, changed_render_checkbox=False):
    colors = []
    opacities = []
    for key in gaussians.num_of_atoms_by_element:
        if global_alpha is not None:
            col = gaussians.num_of_atoms_by_element[key]['color']
            gaussians.num_of_atoms_by_element[key]['color'] = (col[0], col[1], col[2], global_alpha)

        if changed_render_checkbox:
            col = gaussians.num_of_atoms_by_element[key]['color']
            if not gaussians.num_of_atoms_by_element[key]['is_rendered']:
                gaussians.num_of_atoms_by_element[key]['color'] = (col[0], col[1], col[2], 0)
            else:
                gaussians.num_of_atoms_by_element[key]['color'] = (col[0], col[1], col[2], 1)

        if gaussians.num_of_atoms_by_element[key]['color'][3] == 0:
            gaussians.num_of_atoms_by_element[key]['is_rendered'] = False

        elem = gaussians.num_of_atoms_by_element[key]
        col = elem['color']
        num = elem['num']
        colors.append([col[:3]] * num)
        opacities.extend([[col[3]]] * num)

    # flatten list: e.g. [[(1,1,0,1), (0,0,1,1)], []] -> [(1,1,0,1), (0,0,1,1)]
    if len(colors) > 0:
        colors = [[x] for xs in colors for x in xs]
        gaussians.sh = torch.tensor(colors, dtype=torch.float32, device="cuda")
        gaussians.opacity = torch.tensor(opacities, dtype=torch.float32, device="cuda")

        g_renderer.update_gaussian_data(gaussians)
        g_renderer.sort_and_update(g_camera)

def set_radius(gaussians, global_scale=None):
    scales = []
    for key in gaussians.num_of_atoms_by_element:
        if global_scale is not None:
            gaussians.num_of_atoms_by_element[key]['scale'] = global_scale
        elem = gaussians.num_of_atoms_by_element[key]
        scale = elem['scale']
        num = elem['num']
        scales.extend([[scale, scale, scale]] * num)

    gaussians.scale = torch.tensor(scales, dtype=torch.float32, device="cuda")
    g_renderer.update_gaussian_data(gaussians)
    g_renderer.sort_and_update(g_camera)

def main():
    global g_camera, g_renderer, g_renderer_list, g_renderer_idx, g_scale_modifier, g_auto_sort, \
        g_show_control_win, g_show_help_win, g_show_camera_win, \
        g_render_mode, g_render_mode_tables_ogl, g_render_mode_tables_cuda, global_scale, global_alpha, \
        g_render_cov3D, debug_covmat, render_all_elements
        
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

    # gaussian data
    gaussians = util_gau.naive_gaussian()
    update_activated_renderer_state(gaussians)

    # settings
    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        imgui.new_frame()

        gl.glClearColor(0, 0, 0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        update_camera_pose_lazy()
        update_camera_intrin_lazy()

        g_renderer.draw(g_render_cov3D)

        # imgui ui
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("Window", True):
                clicked, g_show_control_win = imgui.menu_item(
                    "Show Control", None, g_show_control_win
                )
                clicked, g_show_help_win = imgui.menu_item(
                    "Show Help", None, g_show_help_win
                )
                clicked, g_show_camera_win = imgui.menu_item(
                    "Show Camera Control", None, g_show_camera_win
                )
                imgui.end_menu()
            imgui.end_main_menu_bar()
        
        if g_show_control_win:
            if imgui.begin("Control", True):

                imgui.core.set_window_font_scale(2.0)

                # rendering backend
                changed, g_renderer_idx = imgui.combo("backend", g_renderer_idx, ["ogl", "cuda"][:len(g_renderer_list)])
                if changed:
                    g_renderer = g_renderer_list[g_renderer_idx]
                    update_activated_renderer_state(gaussians)

                imgui.text(f"fps = {imgui.get_io().framerate:.1f}")

                changed, g_renderer.reduce_updates = imgui.checkbox(
                        "reduce updates", g_renderer.reduce_updates,
                    )

                imgui.text(f"# of Gaus = {len(gaussians)}")

                if imgui.button(label='open CuAl50_Ni'):
                    file_path = '/home/qa43nawu/temp/qa43nawu/out/point_cloud_100K.ply'

                    if file_path:
                        try:
                            gaussians = util_gau.load_ply(file_path)
                            g_renderer.update_gaussian_data(gaussians)
                            g_renderer.sort_and_update(g_camera)
                        except RuntimeError as e:
                            pass

                if imgui.button(label='open CuAl50_Ni COV'):
                    file_path = '/home/qa43nawu/temp/qa43nawu/out/point_cloud_100_COV.ply'

                    if file_path:
                        try:
                            gaussians = util_gau.load_ply(file_path)
                            g_renderer.update_gaussian_data(gaussians)
                            g_renderer.sort_and_update(g_camera)
                        except RuntimeError as e:
                            pass

                if imgui.button(label='open train'):
                    file_path = '/home/qa43nawu/temp/qa43nawu/input_files/trained_data/train/point_cloud/iteration_30000/point_cloud.ply'

                    if file_path:
                        try:
                            gaussians = util_gau.load_ply(file_path)
                            g_renderer.update_gaussian_data(gaussians)
                            g_renderer.sort_and_update(g_camera)
                        except RuntimeError as e:
                            pass

                if imgui.button(label='open ply'):
                    file_path = filedialog.askopenfilename(title="open ply",
                        initialdir="/home/qa43nawu/temp/qa43nawu/out/",
                        filetypes=[('ply file', '.ply')]
                        )
                    if file_path:
                        try:
                            gaussians = util_gau.load_ply(file_path)
                            g_renderer.update_gaussian_data(gaussians)
                            g_renderer.sort_and_update(g_camera)
                        except RuntimeError as e:
                            pass
                
                # camera fov
                changed, g_camera.fovy = imgui.slider_float(
                    "fov", g_camera.fovy, 0.001, np.pi - 0.001, "fov = %.3f"
                )
                changed, g_camera.zoom_sensitivity = imgui.slider_float(
                    "move sensitivity", g_camera.zoom_sensitivity, 0.001, 10, "zoom_sensitivity = %.3f"
                )
                # changed, g_camera.position = imgui.slider_float3(
                #     "camera position", g_camera.position[0], g_camera.position[1], g_camera.position[2], np.pi - 0.001, 10000.0
                # )
                # changed, g_camera.position[2] = imgui.slider_float(
                #     "campos2", g_camera.position[2], 0.001, np.pi - 0.001, "cam_pos = %.3f"
                # )

                g_camera.is_intrin_dirty = changed
                update_camera_intrin_lazy()
                
                # scale modifier
                changed, g_scale_modifier = imgui.slider_float(
                    "", g_scale_modifier, 0, 5, "scale modifier = %.3f"
                )
                imgui.same_line()
                if imgui.button(label="reset"):
                    g_scale_modifier = 1.
                    changed = True
                    
                if changed:
                    g_renderer.set_scale_modifier(g_scale_modifier)

                # render mode
                if g_renderer_idx == 0:  # ogl
                    changed, g_render_mode = imgui.combo("shading", g_render_mode, g_render_mode_tables_ogl)
                else:  # cuda
                    changed, g_render_mode = imgui.combo("shading", g_render_mode, g_render_mode_tables_cuda)

                if changed:
                    if g_renderer_idx == 0:  # ogl
                        g_renderer.set_render_mod(g_render_mode - 4)
                    else:  # cuda
                        g_renderer.set_render_mod(g_render_mode)
                
                # sort button
                if imgui.button(label='sort Gaussians'):
                    g_renderer.sort_and_update(g_camera)
                imgui.same_line()
                changed, g_auto_sort = imgui.checkbox(
                        "auto sort", g_auto_sort,
                    )
                if g_auto_sort:
                    g_renderer.sort_and_update(g_camera)
                
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
                    c1, debug_covmat[0] = imgui.slider_float(f"##cell{0}{0}", debug_covmat[0], -1, 1, format="%.3f")
                    imgui.table_set_column_index(1)
                    c2, debug_covmat[1] = imgui.slider_float(f"##cell{0}{1}", debug_covmat[1], -1, 1, format="%.3f")
                    imgui.table_set_column_index(2)
                    c3, debug_covmat[2] = imgui.slider_float(f"##cell{0}{2}", debug_covmat[2], -1, 1, format="%.3f")

                    imgui.table_next_row()
                    imgui.table_set_column_index(1)
                    c4, debug_covmat[3] = imgui.slider_float(f"##cell{1}{1}", debug_covmat[3], -1, 1, format="%.3f")
                    imgui.table_set_column_index(2)
                    c5, debug_covmat[4] = imgui.slider_float(f"##cell{1}{2}", debug_covmat[4], -1, 1, format="%.3f")

                    imgui.table_next_row()
                    imgui.table_set_column_index(2)
                    c6, debug_covmat[5] = imgui.slider_float(f"##cell{2}{2}", debug_covmat[5], -1, 1, format="%.3f")

                    if c1 or c2 or c3 or c4 or c5 or c6:
                        gaussians.cov3D = np.tile(debug_covmat, (100, 1))
                        g_renderer.update_gaussian_data(gaussians)
                        # print(gaussians.cov3D)

                    imgui.end_table()


                imgui.end()




        if g_show_camera_win:
            imgui.core.set_window_font_scale(2.0)

            if imgui.button(label='rot 180'):
                g_camera.flip_ground()

            changed, g_camera.target_dist = imgui.slider_float(
                    "t", g_camera.target_dist, 1., 8., "target dist = %.3f"
                )
            if changed:
                g_camera.update_target_distance()

            changed, g_camera.rot_sensitivity = imgui.slider_float(
                    "r", g_camera.rot_sensitivity, 0.002, 0.1, "rotate speed = %.3f"
                )
            imgui.same_line()
            if imgui.button(label="reset r"):
                g_camera.rot_sensitivity = 0.02

            changed, g_camera.trans_sensitivity = imgui.slider_float(
                    "m", g_camera.trans_sensitivity, 0.001, 0.2, "move speed = %.3f"
                )
            imgui.same_line()
            if imgui.button(label="reset m"):
                g_camera.trans_sensitivity = 0.01

            changed, g_camera.zoom_sensitivity = imgui.slider_float(
                    "z", g_camera.zoom_sensitivity, 0.001, 0.05, "zoom speed = %.3f"
                )
            imgui.same_line()
            if imgui.button(label="reset z"):
                g_camera.zoom_sensitivity = 0.01

            changed, g_camera.roll_sensitivity = imgui.slider_float(
                    "ro", g_camera.roll_sensitivity, 0.003, 0.1, "roll speed = %.3f"
                )
            imgui.same_line()
            if imgui.button(label="reset ro"):
                g_camera.roll_sensitivity = 0.03

        if g_show_help_win:
            imgui.begin("Help", True)
            imgui.core.set_window_font_scale(2.0)
            imgui.text("Open Gaussian Splatting PLY file \n  by click 'open ply' button")
            imgui.text("Use left click & move to rotate camera")
            imgui.text("Use right click & move to translate camera")
            imgui.text("Press Q/E to roll camera")
            imgui.text("Use scroll to zoom in/out")
            imgui.text("Use control panel to change setting")
            imgui.end()

        if g_show_atom_settings_win:
            if imgui.begin("Atom Settings", True):

                imgui.text('Display settings:')

                changed, g_render_cov3D = imgui.core.checkbox('Render cov3D', g_render_cov3D)
                if changed:
                    g_renderer.need_rerender = True

                imgui.core.push_item_width(500)
                changed, global_alpha = imgui.core.slider_float('Global alpha', global_alpha, 0.0, 1.0)
                if changed:
                    set_colors(gaussians, global_alpha=global_alpha)
                changed, global_scale = imgui.core.slider_float('Global scale', global_scale, 0.0, 1.0)
                if changed:
                    set_radius(gaussians, global_scale=global_scale)

                imgui.text('Element settings:')

                changed, render_all_elements = imgui.core.checkbox('', render_all_elements)
                if changed:
                    changed_render_all_elements(gaussians)
                    # set_colors(gaussians)

                for elem in gaussians.num_of_atoms_by_element:
                    imgui.push_id(elem)
                    imgui.core.set_window_font_scale(2.0)
                    # imgui.table_next_row()
                    # imgui.table_set_column_index(0)

                    changed, gaussians.num_of_atoms_by_element[elem]['is_rendered'] = imgui.core.checkbox('', gaussians.num_of_atoms_by_element[elem]['is_rendered'])

                    if changed:
                        set_colors(gaussians, changed_render_checkbox=True)

                    imgui.same_line()

                    imgui.text(elem)
                    imgui.same_line(80, 50)

                    imgui.text(str(gaussians.num_of_atoms_by_element[elem]['num']))
                    imgui.same_line(200, 50)

                    imgui.core.push_item_width(500)

                    # imgui.table_set_column_index(1)
                    changed, gaussians.num_of_atoms_by_element[elem]['color'] = imgui.core.color_edit4('', *gaussians.num_of_atoms_by_element[elem]['color'])

                    if changed:
                        set_colors(gaussians)

                    # imgui.table_set_column_index(2)
                    imgui.same_line(spacing=50)

                    imgui.core.push_item_width(200)
                    changed, gaussians.num_of_atoms_by_element[elem]['scale'] = imgui.core.slider_float('', gaussians.num_of_atoms_by_element[elem]['scale'], 0.0, 10.0)
                    imgui.pop_id()


                    if changed:
                        set_radius(gaussians)

                # imgui.end_table()
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
