from typing import Any, List, Tuple

from aqt import mw
from aqt.browser.previewer import Previewer
from aqt.clayout import CardLayout
from aqt.gui_hooks import (
    reviewer_will_show_context_menu,
    state_shortcuts_will_change,
    webview_will_set_content,
)
from aqt.qt import *
from aqt.reviewer import Reviewer
from aqt.webview import WebContent

from .playback_controller import PlaybackController

config = mw.addonManager.getConfig(__name__)
playback_controller = PlaybackController(config)
mw.playback_controller = playback_controller
mw.addonManager.setWebExports(__name__, r"web/.*\.js")
base_path = f"/_addons/{mw.addonManager.addonFromModule(__name__)}/web"


def append_webcontent(webcontent: WebContent, context: Any) -> None:
    if isinstance(context, (Reviewer, Previewer, CardLayout)):
        webcontent.js.append(f"{base_path}/audio.js")


actions = [
    ("Speed Up Audio", config["speed_up_shortcut"], playback_controller.speed_up),
    ("Slow Down Audio", config["slow_down_shortcut"], playback_controller.slow_down),
    (
        "Reset Audio Speed",
        config["reset_speed_shortcut"],
        playback_controller.reset_speed,
    ),
    ("Play Next Audio", config["play_next_shortcut"], playback_controller.play_next),
    (
        "Play Previous Audio",
        config["play_previous_shortcut"],
        playback_controller.play_previous,
    ),
]


def add_state_shortcuts(state: str, shortcuts: List[Tuple[str, Callable]]) -> None:
    if state == "review":
        for (label, shortcut, cb) in actions:
            shortcuts.append((shortcut, cb))


def add_menu_items(reviewer: Reviewer, menu: QMenu) -> None:
    for (label, shortcut, cb) in actions:
        action = menu.addAction(label)
        action.setShortcut(shortcut)
        qconnect(action.triggered, cb)


playback_controller.init_hooks()
state_shortcuts_will_change.append(add_state_shortcuts)
webview_will_set_content.append(append_webcontent)
reviewer_will_show_context_menu.append(add_menu_items)
