from typing import List, Tuple

import aqt
import aqt.sound
from aqt.qt import *
from aqt import mw
from aqt.gui_hooks import reviewer_will_show_context_menu, state_shortcuts_will_change
from aqt.utils import tooltip

config = mw.addonManager.getConfig(__name__)


def get_speed() -> float:
    return aqt.sound.mpvManager.command("get_property", "speed")


def get_speed_factor() -> float:
    return float(config.get("speed_factor", 10)) / 100


def add_speed(speed: float):
    aqt.sound.mpvManager.command("add", "speed", speed)
    tooltip(f"Audio Speed {speed:+}<br>Current Speed: {get_speed()}")


def set_speed(speed: float):
    aqt.sound.mpvManager.command("set_property", "speed", speed)
    tooltip(f"Reset Speed: {get_speed()}")


def reset_speed():
    set_speed(1.0)


def speed_up():
    add_speed(get_speed_factor())


def slow_down():
    add_speed(-get_speed_factor())


actions = [
    ("Speed Up Audio", config["speed_up_shortcut"], speed_up),
    ("Slow Down Audio", config["slow_down_shortcut"], slow_down),
    ("Reset Audio Speed", config["reset_speed_shortcut"], reset_speed),
]


def add_state_shortcuts(state: str, shortcuts: List[Tuple[str, Callable]]) -> None:
    if state == "review":
        for (label, shortcut, cb) in actions:
            shortcuts.append((shortcut, cb))


def add_menu_items(reviewer, menu: QMenu):
    for (label, shortcut, cb) in actions:
        action = menu.addAction(label)
        action.setShortcut(shortcut)
        qconnect(action.triggered, cb)


reviewer_will_show_context_menu.append(add_menu_items)
state_shortcuts_will_change.append(add_state_shortcuts)
