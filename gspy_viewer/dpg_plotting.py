import dearpygui.dearpygui as dpg

plotting_data = {
    "points": [[0.0, 0.0], [0.25, 0.25], [0.5, 0.5], [0.75, 0.75], [1.0, 1.0]],
    "volume_min_max": [0.0, 0.0],
    "volume_alpha_range": [0.0, 0.0]
}

def value_updated(sender, app_data, user_data):
    print(app_data)

def update_plot():
    """Updates the plot based on current control points."""
    dpg.set_value("line_series", [list(p) for p in plotting_data["points"]])


def update_gaussian_data(gaussians):
    pass

def interpolate_y_value(x_value):
    """Finds the y-value for a given x-value using linear interpolation."""
    # Sort points by x to ensure interpolation works
    sorted_points = sorted(plotting_data["points"], key=lambda p: p[0])

    for i in range(len(sorted_points) - 1):
        x0, y0 = sorted_points[i]
        x1, y1 = sorted_points[i + 1]

        # If x_value lies between x0 and x1, do linear interpolation
        if x0 <= x_value <= x1:
            t = (x_value - x0) / (x1 - x0)
            return y0 + t * (y1 + t * (y1 - y0))  # Linear interpolation formula

    return None  # x_value is out of bounds

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


def open_plotting_window(gaussians):
    dpg.create_context()
    dpg.create_viewport(title='Individual alpha', width=2500, height=1200)
    dpg.set_global_font_scale(2)
    with dpg.window(label="Volume histogram"):
        with dpg.plot(label="##Volume histogram", width=1100, height=1000):
            dpg.add_plot_axis(dpg.mvXAxis, label="Volume")
            dpg.add_plot_axis(dpg.mvYAxis, label="Frequency")

            data = gaussians.volume_opacity
            dpg.add_histogram_series(data, bins=1000, label="histogram", parent=dpg.last_item(),
                                     max_range=gaussians.volume_opacity.max())

            dpg.add_drag_line(label="Alpha = 0", color=[255, 0, 0, 255], default_value=10, thickness=3)
            dpg.add_drag_line(label="Alpha = 1", color=[255, 0, 0, 255], default_value=100, thickness=3)

    with dpg.window(label="Set opacity depending on volume", pos=[1200, 0]):
        draw_linear_mapping()

        dpg.add_slider_float(label='test', default_value=1.0, callback=value_updated)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()