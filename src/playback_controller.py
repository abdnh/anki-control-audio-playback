import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Match, Optional, Tuple

import aqt
import aqt.sound
from anki.cards import Card
from anki.sound import AVTag, SoundOrVideoTag
from aqt import mw
from aqt.browser.previewer import Previewer
from aqt.clayout import CardLayout
from aqt.gui_hooks import (av_player_did_begin_playing,
                           av_player_did_end_playing,
                           reviewer_will_play_answer_sounds,
                           reviewer_will_play_question_sounds,
                           webview_did_receive_js_message)
from aqt.qt import *
from aqt.qt import QApplication
from aqt.sound import AVTag, av_player
from aqt.utils import tooltip
from aqt.webview import AnkiWebView


def get_active_webview() -> AnkiWebView:
    dialog = QApplication.activeModalWidget()
    if isinstance(dialog, CardLayout):
        return dialog.preview_web
    window = QApplication.activeWindow()
    if isinstance(window, Previewer):
        return window._web  # pylint: disable=protected-access
    return mw.reviewer.web


@dataclass
class SoundTagInfo:
    side: str
    index: int
    tag: AVTag


FILTER_NAME = "playback_controller"
SOUND_REF_RE = re.compile(r"\[sound:(.*?)\]")
PLAY_BUTTON = """<a class="replay-button soundLink" href=# onclick="pycmd('{cmd}:{side}:{idx}'); return false;">
    <svg class="playImage" viewBox="0 0 64 64" version="1.1">
        <circle cx="32" cy="32" r="29" />
        <path d="M56.502,32.301l-37.502,20.101l0.329,-40.804l37.173,20.703Z" />
    </svg>
</a>"""


class SoundTagList:
    def __init__(self) -> None:
        self.qtags: List[AVTag] = []
        self.atags: List[AVTag] = []

    def get_side(self, side: str) -> List[AVTag]:
        if side == "q":
            return self.qtags
        else:
            return self.atags


class PlaybackController:
    def __init__(self, config: Dict):
        self.config = config
        self.sound_tags = SoundTagList()
        self.extra_tags = SoundTagList()
        self.current_sound: Optional[SoundTagInfo] = SoundTagInfo(
            side="q", index=0, tag=SoundOrVideoTag(filename="")
        )

    def get_speed(self) -> float:
        return aqt.sound.mpvManager.command("get_property", "speed")

    def get_speed_factor(self) -> float:
        return float(self.config.get("speed_factor", 10)) / 100

    def add_speed(self, speed: float) -> None:
        aqt.sound.mpvManager.command("add", "speed", speed)
        tooltip(f"Audio Speed {speed:+}<br>Current Speed: {self.get_speed()}")

    def set_speed(self, speed: float) -> None:
        aqt.sound.mpvManager.command("set_property", "speed", speed)
        tooltip(f"Reset Speed: {self.get_speed()}")

    def reset_speed(self) -> None:
        self.set_speed(1.0)
        get_active_webview().eval("resetAudioSpeeed();")

    def speed_up(self) -> None:
        factor = self.get_speed_factor()
        self.add_speed(factor)
        get_active_webview().eval(f"addAudioPlaybackRate({factor});")

    def slow_down(self) -> None:
        factor = -self.get_speed_factor()
        self.add_speed(factor)
        get_active_webview().eval(f"addAudioPlaybackRate({factor});")

    def save_question_sound_tags(self, card: Card, tags: List[AVTag]) -> None:
        self.sound_tags.qtags = tags.copy()
        self.extra_tags.qtags = []

    def save_answer_sound_tags(self, card: Card, tags: List[AVTag]) -> None:
        self.sound_tags.atags = tags.copy()
        self.extra_tags.atags = []

    def on_began_playing(self, player: aqt.sound.Player, tag: AVTag) -> None:
        idx = -1
        side = ""
        tag_dict = {
            "a": self.sound_tags.atags + self.extra_tags.atags,
            "q": self.sound_tags.qtags + self.extra_tags.qtags,
        }
        for key, tags in tag_dict.items():
            try:
                idx = tags.index(tag)
                side = key
                break
            except ValueError:
                pass
        if not side:
            return
        print(f"on_began_playing: {side=} {idx=}")
        get_active_webview().eval(
            "setTimeout(() => setPlayButtonHighlight({}, {}, {}), 100);".format(
                json.dumps(side),
                json.dumps(idx),
                json.dumps(self.config["play_button_highlight_color"]),
            )
        )
        self.current_sound = SoundTagInfo(side, idx, tag)

    def clear_sound_tag_highlight(self, player: aqt.sound.Player) -> None:
        get_active_webview().eval(
            """
            setTimeout(clearPlayButtonsHighlight, 100);
            """
        )

    # FIXME: queue can be get 'stuck' in only one side even when the option to include both sides's sounds in the back is enabled
    # we probably need to monkey-patch Reviewer.replayAudio to work around this.

    def play_n(self, i: int) -> None:
        if av_player._enqueued:
            # if there are any queued sounds, interrupt the current sound and continue playing the next ones
            side = self.current_sound.side
            tags = self.sound_tags.get_side(side) + self.extra_tags.get_side(side)
            next_tags = tags[self.current_sound.index + i :]
            av_player.play_tags(next_tags)
        else:
            av_player._stop_if_playing()
            side = self.current_sound.side
            tags = self.sound_tags.get_side(side) + self.extra_tags.get_side(side)
            if tags:
                idx = (self.current_sound.index + i) % len(tags)
                av_player.play_tags([tags[idx]])

    def play_next(self) -> None:
        self.play_n(1)

    def play_previous(self) -> None:
        self.play_n(-1)

    # def replay_audios(self) -> None:
    #     reviewer = mw.reviewer
    #     card = reviewer.card
    #     if mw.reviewer.state == "question":
    #         tags = card.question_av_tags()
    #         self.sound_tags.qtags = tags
    #         tags += self.extra_tags.qtags
    #     else:
    #         extra_tags = []
    #         def_tags = []
    #         if card.replay_question_audio_on_answer_side():
    #             def_tags += card.question_av_tags()
    #             extra_tags += self.extra_tags.qtags
    #         def_tags += self.extra_tags.atags
    #         extra_tags += self.extra_tags.atags
    #         self.sound_tags.atags = def_tags
    #         tags = extra_tags + def_tags
    #     print(f"replay_audios: {tags=}")
    #     av_player.play_tags(tags)
    #     # reviewer.replayAudio()

    # def modify_replay(self, state: str, shortcuts: List[Tuple[str, Callable]]) -> None:
    #     if state == "review":
    #         # modify the 'r' shortcut to give us replayed audios
    #         for i, shortcut in enumerate(shortcuts):
    #             if shortcut[0] == "r":
    #                 shortcuts[i] = (shortcut[0], lambda: self.replay_audios())

    def handle_js_msg(
        self, handled: Tuple[bool, Any], message: str, context: Any
    ) -> Tuple[bool, Any]:
        if not message.startswith(FILTER_NAME):
            return handled
        _, subcmd, data = message.split(":", maxsplit=2)
        if subcmd == "play":
            filename = data
            av_player.play_file(filename)
        return (True, None)

    def add_sound_tags_from_text(
        self, text: str, side: str, play: bool = False
    ) -> Tuple[str, List[AVTag]]:
        tags = self.sound_tags.get_side(side) + self.extra_tags.get_side(side)
        added: List[AVTag] = []

        def repl_sounds(match: Match) -> str:
            filename = match.group(1)
            tag = SoundOrVideoTag(filename=filename)
            added.append(tag)
            return PLAY_BUTTON.format(
                cmd="play", idx=len(tags) + len(added) - 1, side=side
            )

        text = SOUND_REF_RE.sub(repl_sounds, text)
        self.extra_tags.get_side(side).extend(added)
        if play:
            av_player._enqueued.extend(added)
            av_player._play_next_if_idle()
        return text, added

    def apply_to_card_avtags(self, card: Card):
        t = card.question_av_tags()
        t.clear()
        t.extend(self.sound_tags.qtags + self.extra_tags.qtags)
        t = card.answer_av_tags()
        t.clear()
        t.extend(self.sound_tags.atags + self.extra_tags.atags)

    def init_hooks(self) -> None:
        av_player_did_begin_playing.append(
            lambda player, tag: self.on_began_playing(player, tag)
        )
        av_player_did_end_playing.append(
            lambda player: self.clear_sound_tag_highlight(player)
        )
        reviewer_will_play_question_sounds.append(
            lambda card, tags: self.save_question_sound_tags(card, tags)
        )
        reviewer_will_play_answer_sounds.append(
            lambda card, tags: self.save_answer_sound_tags(card, tags)
        )
        # state_shortcuts_will_change.append(
        #     lambda state, shortcuts: self.modify_replay(state, shortcuts)
        # )
        webview_did_receive_js_message.append(
            lambda handled, msg, context: self.handle_js_msg(handled, msg, context)
        )
