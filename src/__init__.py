from dataclasses import dataclass
import json
from typing import Dict, List, Optional, Tuple, Any

import aqt
import aqt.sound
from aqt.sound import AVTag, av_player

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


# FIXME: queue can be get 'stuck' in only one side even when the option to include both sides's sounds in the back is enabled
# we probably need to monkey-patch Reviewer.replayAudio to work around this.


def play_n(i: int) -> None:
    if av_player._enqueued:
        av_player.clear_queue_and_maybe_interrupt()
        # if there are any queued sounds, interrupt the current sound and continue playing the next ones
        next_tags = sound_tags[current_sound.side][current_sound.index + i :]
        av_player.play_tags(next_tags)
    else:
        av_player._stop_if_playing()
        side = current_sound.side
        tags = sound_tags[side]
        idx = (current_sound.index + i) % len(tags)
        av_player.play_tags([tags[idx]])


def play_next() -> None:
    play_n(1)


def play_previous() -> None:
    play_n(-1)


actions = [
    ("Speed Up Audio", config["speed_up_shortcut"], speed_up),
    ("Slow Down Audio", config["slow_down_shortcut"], slow_down),
    ("Reset Audio Speed", config["reset_speed_shortcut"], reset_speed),
    ("Play Next Audio", config["play_next_shortcut"], play_next),
    ("Play Previous Audio", config["play_previous_shortcut"], play_previous),
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


sound_tags: Dict[str, List[AVTag]] = {
    "a": [],
    "q": [],
}


@dataclass
class SoundTagInfo:
    side: str
    index: int
    tag: AVTag


current_sound: Optional[SoundTagInfo]


def save_question_sound_tags(card: Card, tags: List[AVTag]) -> None:
    global sound_tags
    sound_tags["q"] = tags


def save_answer_sound_tags(card: Card, tags: List[AVTag]) -> None:
    global sound_tags
    sound_tags["a"] = tags


def on_begin_playing(player: aqt.sound.Player, tag: AVTag) -> None:
    idx = -1
    side = ""
    for key, tags in sound_tags.items():
        try:
            idx = tags.index(tag)
            side = key
            break
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

    global current_sound
    current_sound = SoundTagInfo(side, idx, tag)


def clear_sound_tag_highlight(player: aqt.sound.Player) -> None:
    mw.reviewer.web.eval(
        """
        setTimeout(clearPlayButtonsHighlight, 100);
        """
    )


reviewer_will_show_context_menu.append(add_menu_items)
state_shortcuts_will_change.append(add_state_shortcuts)
webview_will_set_content.append(append_webcontent)
av_player_did_begin_playing.append(on_begin_playing)
av_player_did_end_playing.append(clear_sound_tag_highlight)
reviewer_will_play_question_sounds.append(save_question_sound_tags)
reviewer_will_play_answer_sounds.append(save_answer_sound_tags)
