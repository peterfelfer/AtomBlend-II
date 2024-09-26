import dearpygui.dearpygui as dpg
import torch
import numpy as np

plotting_data = {
    "points": [[0.0, 0.0], [0.25, 0.25], [0.5, 0.5], [0.75, 0.75], [1.0, 1.0]],
    "volume_min_max": [0.0, 0.0],
    # "volume_alpha_range": [0.0, 0.0]
}

def value_updated(sender, app_data, user_data):
    print(sender, app_data, user_data)
    print(dpg.get_value(sender))

def update_plot():
    """Updates the plot based on current control points."""
    dpg.set_value("line_series", [list(p) for p in plotting_data["points"]])


def update_volumes(sender, app_data, user_data):
    line_id = user_data[0]
    gaussians = user_data[1]
    g_renderer = user_data[2]

    val = dpg.get_value(sender)
    if val is not None:
        if plotting_data["volume_min_max"][line_id] == val:
            return

        plotting_data["volume_min_max"][line_id] = val
    else:
        return

    new_volumes = []
    for volume in gaussians.g_volume:

        if volume.item() < plotting_data["volume_min_max"][0]:
            new_volume = 0.0
        elif volume.item() > plotting_data["volume_min_max"][1]:
            new_volume = 0.0
        else:
            new_volume = interpolate_y_value(volume.item())

        new_volumes.append([new_volume])

    # update line series data
    min = plotting_data["volume_min_max"][0]
    max = plotting_data["volume_min_max"][1]
    x_values = [min, max]
    y_values = [0, 1]
    dpg.set_value('alpha_line', [x_values, y_values])

    gaussians.opacity = torch.tensor(np.array(new_volumes)).float().cuda().requires_grad_(False)
    g_renderer.update_gaussian_data(gaussians)
    # g_renderer.need_rerender = True

def interpolate_y_value(x_value):
    # # Sort points by x to ensure interpolation works
    # sorted_points = sorted(plotting_data["points"], key=lambda p: p[0])
    #
    # for i in range(len(sorted_points) - 1):
    x0, y0 = [plotting_data["volume_min_max"][0], 0.0]
    x1, y1 = [plotting_data["volume_min_max"][1], 1.0]

    if x0 <= x_value <= x1:
        t = (x_value - x0) / (x1 - x0)
        return y0 + t * (y1 + t * (y1 - y0))

def on_point_drag(sender, app_data, user_data):
    """Updates control point when dragged."""
    point_idx = user_data
    plotting_data["points"][point_idx] = app_data
    update_plot()

def draw_linear_mapping():
    with dpg.plot(label="Alpha depending on volume", width=1100, height=1000):
        dpg.add_plot_axis(dpg.mvXAxis, label="Volume")
        # dpg.add_plot_axis(dpg.mvYAxis, label="Alpha")

        dpg.add_drag_point(label="Lower alpha", color=[0, 255, 0, 255])

        x_vals, y_vals = zip(*plotting_data["points"])
        with dpg.plot_axis(dpg.mvYAxis, label="Alpha"):
            dpg.add_line_series(x_vals, y_vals, label="Alpha Function", parent=dpg.last_item(), id="line_series")

        for i, (x, y) in enumerate(plotting_data["points"]):
            dpg.add_drag_point(label=f"Point", default_value=[x, y], callback=on_point_drag, user_data=i)


def open_plotting_window(gaussians, g_renderer):
    dpg.create_context()
    dpg.create_viewport(title='Individual alpha', width=2500, height=1200)
    dpg.set_global_font_scale(2)
    min = plotting_data["volume_min_max"][0]
    max = plotting_data["volume_min_max"][1]

    with dpg.window(label="Volume histogram"):
        with dpg.plot(label="##Volume histogram", width=1100, height=1000):
            dpg.add_plot_axis(dpg.mvXAxis, label="Volume")
            with dpg.plot_axis(dpg.mvYAxis, label="Frequency", tag="y1"):
                data = gaussians.g_volume
                dpg.add_histogram_series(data, bins=1000, label="histogram", parent=dpg.last_item(),
                                         max_range=gaussians.g_volume.max())

            dpg.add_drag_line(label="Alpha = 0", color=[255, 0, 0, 255], default_value=min, thickness=3, callback=update_volumes, user_data=[0, gaussians, g_renderer])
            dpg.add_drag_line(label="Alpha = 1", color=[255, 0, 0, 255], default_value=max, thickness=3, callback=update_volumes, user_data=[1, gaussians, g_renderer])

            # dpg.add_plot_axis(dpg.mvXAxis2, label="x2", tag="x2_axis")

            with dpg.plot_axis(dpg.mvYAxis2, label="Alpha", tag="y2", opposite=True):
                dpg.add_line_series([min, max], [0, 1], label="alpha", parent="y2", tag="alpha_line")

    with dpg.window(label="Set opacity depending on volume", pos=[1200, 0]):
        draw_linear_mapping()

        dpg.add_slider_float(label='test', default_value=1.0, callback=value_updated)

    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

