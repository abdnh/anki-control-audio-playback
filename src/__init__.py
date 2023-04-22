from typing import Any, List, Tuple

import aqt
import aqt.sound
from aqt import gui_hooks, mw
from aqt.qt import *
from aqt.reviewer import Reviewer
from aqt.utils import showWarning, tooltip
from aqt.webview import WebContent

config = mw.addonManager.getConfig(__name__)
mw.addonManager.setWebExports(__name__, r"web/.*\.js")
base_path = f"/_addons/{mw.addonManager.addonFromModule(__name__)}/web"


def append_webcontent(webcontent: WebContent, context: Any) -> None:
    if isinstance(context, Reviewer):
        webcontent.js.append(f"{base_path}/audio.js")


def get_speed() -> float:
    return aqt.sound.mpvManager.command("get_property", "speed")


def get_speed_factor() -> float:
    return float(config.get("speed_factor", 10)) / 100


def add_speed(speed: float) -> None:
    aqt.sound.mpvManager.command("add", "speed", speed)
    tooltip(f"Audio Speed {speed:+}<br>Current Speed: {get_speed()}")


def set_speed(speed: float) -> None:
    aqt.sound.mpvManager.command("set_property", "speed", speed)
    tooltip(f"Reset Speed: {get_speed()}")


def reset_speed() -> None:
    set_speed(1.0)
    if mw.reviewer:
        mw.reviewer.web.eval("resetAudioSpeeed();")


def speed_up() -> None:
    factor = get_speed_factor()
    add_speed(factor)
    if mw.reviewer:
        mw.reviewer.web.eval(f"addAudioPlaybackRate({factor});")


def slow_down() -> None:
    factor = -get_speed_factor()
    add_speed(factor)
    if mw.reviewer:
        mw.reviewer.web.eval(f"addAudioPlaybackRate({factor});")


actions = [
    ("Speed Up Audio", config["speed_up_shortcut"], speed_up),
    ("Slow Down Audio", config["slow_down_shortcut"], slow_down),
    ("Reset Audio Speed", config["reset_speed_shortcut"], reset_speed),
]


def add_state_shortcuts(state: str, shortcuts: List[Tuple[str, Callable]]) -> None:
    if state == "review":
        for label, shortcut, cb in actions:
            shortcuts.append((shortcut, cb))


def add_menu_items(reviewer: Reviewer, menu: QMenu) -> None:
    for label, shortcut, cb in actions:
        action = menu.addAction(label)
        action.setShortcut(shortcut)
        qconnect(action.triggered, cb)


def on_profile_did_open() -> None:
    if aqt.sound.mpvManager:
        gui_hooks.reviewer_will_show_context_menu.append(add_menu_items)
        gui_hooks.state_shortcuts_will_change.append(add_state_shortcuts)
        gui_hooks.webview_will_set_content.append(append_webcontent)
    else:
        showWarning(
            "This add-on only works with the mpv media player.",
            title="Audio Playback Controls",
        )


gui_hooks.profile_did_open.append(on_profile_did_open)
