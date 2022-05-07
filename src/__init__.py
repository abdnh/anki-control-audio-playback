import json
from typing import List, Tuple, Any

import aqt
import aqt.sound
from aqt.sound import AVTag

from aqt.qt import *
from aqt import mw
from aqt.gui_hooks import (
    reviewer_will_show_context_menu,
    state_shortcuts_will_change,
    webview_will_set_content,
    av_player_did_begin_playing,
    av_player_did_end_playing,
    reviewer_will_play_answer_sounds,
    reviewer_will_play_question_sounds,
)
from aqt.utils import tooltip
from aqt.webview import WebContent
from aqt.reviewer import Reviewer
from anki.cards import Card


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


def add_speed(speed: float):
    aqt.sound.mpvManager.command("add", "speed", speed)
    tooltip(f"Audio Speed {speed:+}<br>Current Speed: {get_speed()}")


def set_speed(speed: float):
    aqt.sound.mpvManager.command("set_property", "speed", speed)
    tooltip(f"Reset Speed: {get_speed()}")


def reset_speed():
    set_speed(1.0)
    if mw.reviewer:
        mw.reviewer.web.eval("resetAudioSpeeed();")


def speed_up():
    factor = get_speed_factor()
    add_speed(factor)
    if mw.reviewer:
        mw.reviewer.web.eval(f"addAudioPlaybackRate({factor});")


def slow_down():
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
        for (label, shortcut, cb) in actions:
            shortcuts.append((shortcut, cb))


def add_menu_items(reviewer, menu: QMenu):
    for (label, shortcut, cb) in actions:
        action = menu.addAction(label)
        action.setShortcut(shortcut)
        qconnect(action.triggered, cb)


sound_tags = {
    "q": [],
    "a": [],
}


def save_question_sound_tags(card: Card, tags: List[AVTag]) -> None:
    global sound_tags
    sound_tags["q"] = tags


def save_answer_sound_tags(card: Card, tags: List[AVTag]) -> None:
    global sound_tags
    sound_tags["a"] = tags


def highlight_playing_tag(player: aqt.sound.Player, tag: AVTag) -> None:
    idx = -1
    side = ""
    for key, tags in sound_tags.items():
        try:
            idx = tags.index(tag)
            side = key
        except ValueError:
            pass
    if not side:
        return

    mw.reviewer.web.eval(
        "setTimeout(() => setPlayButtonHighlight({}, {}, {}), 100);".format(
            json.dumps(side),
            json.dumps(idx),
            json.dumps(config["play_button_highlight_color"]),
        )
    )


def clear_sound_tag_highlight(player: aqt.sound.Player) -> None:
    mw.reviewer.web.eval(
        """
        setTimeout(clearPlayButtonsHighlight, 100);
        """
    )


reviewer_will_show_context_menu.append(add_menu_items)
state_shortcuts_will_change.append(add_state_shortcuts)
webview_will_set_content.append(append_webcontent)
av_player_did_begin_playing.append(highlight_playing_tag)
av_player_did_end_playing.append(clear_sound_tag_highlight)
reviewer_will_play_question_sounds.append(save_question_sound_tags)
reviewer_will_play_answer_sounds.append(save_answer_sound_tags)
