

from talon import noise, ctrl, actions, ui
from talon_plugins import eye_mouse, eye_zoom_mouse
from talon_plugins.eye_mouse import config, toggle_camera_overlay, toggle_control

def pop_handler(active: bool):
    if ((eye_zoom_mouse.zoom_mouse.enabled == False) and (config.control_mouse == False)):
        ctrl.mouse_click(button=0, hold=16000)
noise.register("pop", pop_handler)


def on_hiss(active: bool):
    if ui.active_app().name != "Code" and "Google Docs" not in ui.active_window().title:
        if active:
            actions.user.mouse_scroll_down(amount=.8)
noise.register("hiss", on_hiss)
