from talon import Module, actions, cron, scope, Context, settings
import time
from typing import TypedDict


"""
This script works by setting a dictionary based on the button state.  If the button is pushed down, the dictionary updated with a 'True' Boolean value. The dictionary is then read using a cron job. The corresponding function is then called based on the dictionary state.  Certain functions can be called in repetition.  These functions are called asynchronous. We don't have to wait for them to return to call them again. (i.e. scrolling down, or pressing a key)

Other functions are called synchronous, these functions cannot be called in repetition and must wait for the others to finish.  Such an example could include waiting on an API call. As a result, the user has to manually set whether or not to force a synchronous or an asynchronous call.  Synchronous calls can only be called on the button up and not the button down since the button down is called both full times as long as it is held down.
"""

mod = Module()
# We use this state variable to make sure we aren't 
# calling the button up command after holding it down
wasHeld = False

class KeyMap(TypedDict):
    left: bool
    right: bool
    center: bool

map: KeyMap = {
    "left": False,
    "right": False,
    "center": False
}



#  By default  this is false which signifies a continuously called function 
# (Holding down scroll etc)
force_synchronous = mod.setting(
    "force_synchronous",
    type=bool,
    default=False, 
    desc="force_synchronous",
)

#  turns just the center button into a synchronous option
force_synchronous_center = mod.setting(
    "force_synchronous_center",
    type=bool,
    default=True,
    desc="force_synchronous_center",
)

button_scroll_amount=mod.setting(
    "button_scroll_amount",
    type=float,
    default=0.1,
    desc="button_scroll_amount",
)

ctx = Context()

def on_interval() -> None:

    # if map contains at least 2 true values, then we have a double keypress
    if two_keypress():

        if map["left"] and map["right"]:
            
            actions.user.left_right_down()
        elif map["left"] and map["center"]:
            actions.user.left_center_down()
        elif map["center"] and map["right"]:
            actions.user.center_right_down()
    
        reset_map()
        return  

    # with synchronous code we only call functions on the button up
    # button down functions  can be asynchronous and held down to repeat,
    #  which is impossible if we have to force synchronous
    if settings.get("user.force_synchronous"):
        return

    if map["center"] and not settings.get("user.force_synchronous_center"):
        actions.user.center_down()
    elif map["left"]:
        actions.user.left_down()
    elif map["right"]:
        actions.user.right_down()

reset_map = lambda: map.update({k: False for k in map.keys()})
two_keypress = lambda: sum(map.values()) >= 2

cron.interval("16ms", on_interval)

@mod.action_class
class Actions:

    def button_down(key: str):
        """Map the key name to down"""
        map[key]=True


    def button_up(key: str):
        """button up"""
        # If you have a synchronous double keypress that has already reset the map, then we don't want to do anything.
        # this prevents single actions mistakenly firing after the double action
        global wasHeld
        if map[key] == False or wasHeld:
            wasHeld = False
            return
        else: 
            map[key]=False


        # if we have a  discrete action that needs to block (wait for return) and can't be asynchronous, 
        # then we can't use the cron job for quick calls in succession and as a result we have to do 
        # it synchronously on the button raise to only call it once
        if settings.get("user.force_synchronous") == True:
            match key:
                case "left":
                    actions.user.left_up( )
                case "right":
                    actions.user.right_up( )
                case "center":
                    actions.user.center_up()

        elif settings.get("user.force_synchronous_center") == True and key == "center":
            actions.user.center_up()

    def left_center_right_down():
        """Left, Center and Right button"""

    def center_right_down():
        """Center and Right button"""
        ctx.settings['user.button_scroll_amount'] = 0.2
        print("Speed reset to 0.2")


    def left_right_down():
        """Left and Right button"""
        ctx.settings['user.button_scroll_amount'] = settings.get("user.button_scroll_amount")
        ctx.settings['user.button_scroll_amount']+=0.2
        print(f'Speed set to: {ctx.settings["user.button_scroll_amount"]}')

    def left_center_down():
        """Left and Center button"""


    def left_down():
        """Left button"""
        actions.user.mouse_scroll_down(button_scroll_amount.get())

    def right_down():
        """Right button"""
        actions.user.mouse_scroll_up(button_scroll_amount.get())
    def center_down():
        """Center button"""
        # modes = scope.get("mode")
        # if "sleep" in modes:
        #     # mode = "sleep"
        #     actions.speech.enable()
        # else:    
        #     actions.speech.disable()
        # time.sleep(2)

    # default implementations to override contextually
    def left_up():
        """Left button up"""
    def right_up():
        """Right button up"""
    def center_up():
        """Center button up"""
        modes = scope.get("mode")
        if "sleep" in modes:
            # mode = "sleep"
            actions.speech.enable()
        else:    
            actions.speech.disable()

    def held_left():
        """ called when the left button is held down"""
    def held_right():
        """ called when the right button is held down"""
    def held_center():
        """ called when the right button is held down"""
        print("Held center")
        global teamNotOutlook
        teamNotOutlook = not teamNotOutlook
        chrome = actions.user.get_running_app("Chrome")
        actions.user.switcher_focus_app(chrome)
        if teamNotOutlook:
            actions.key("ctrl-shift-6")
        else:
            actions.key("ctrl-shift-7")

# Trigger a hold if a key has been held for SEC_TO_TRIGGER seconds
# check if this threshold is met every SEC_TO_CHECK seconds
CHECK_INTERVAL = .5
SEC_TO_TRIGGER = 2
teamNotOutlook=False

class KeyHold(TypedDict): 
    left: float
    right: float
    center: float

held_seconds:  KeyHold = {
    'left': 0,
    'right': 0,
    'center': 0
} 
reset_hold = lambda: held_seconds.update({k: 0 for k in held_seconds.keys()})

def button_held_down() -> None:

    for buttonDirection in map:
        isHeldDown = map[buttonDirection]
        if isHeldDown == True:
            held_seconds[buttonDirection] += CHECK_INTERVAL
        else:
            held_seconds[buttonDirection] = 0
    
        if held_seconds[buttonDirection] == SEC_TO_TRIGGER:
            # We reset the hold time so we can potentially trigger the action again after the trigger time passes once more.
            
            reset_hold()

            # we only want to trigger on synchronous actions since if it was asynchronous We might trigger it by mistake, 
            # for instance if you were scrolling down a lot and end up holding the button for 5 seconds

            if settings.get("user.force_synchronous_center") and buttonDirection == "center":
                actions.user.held_center()
                
            elif settings.get("user.force_synchronous"):
                print(f'{buttonDirection} hold triggered')

                match buttonDirection:
                    case "right":
                        actions.user.held_right()
                    case "center":
                        actions.user.held_center()
                    case "left":
                        actions.user.held_left()
            else: 
                return
            
            # we need to reset the map so we don't call the up function
            # as well on release of the button
            reset_map()
            global wasHeld
            wasHeld = True
            


check_freq_cron_format = str(int(CHECK_INTERVAL * 1000))
cron.interval(f'{check_freq_cron_format}ms', button_held_down)