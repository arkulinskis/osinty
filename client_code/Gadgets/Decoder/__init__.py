import re

from anvil import *
from anvil.js import window

from ._anvil_designer import DecoderTemplate
from ... import gadget_kit, state


def _fmt(ms):
    """[UTC text, local text] for a time in milliseconds, or None."""
    d = window.Date(ms)
    if window.isNaN(d.getTime()):
        return None
    utc = re.sub(r"\.\d+Z$", " UTC", str(d.toISOString()).replace("T", " "))
    return [utc, str(d.toLocaleString()) + " (your time)"]


class Decoder(DecoderTemplate):
    """Turn social-media post IDs (snowflakes) and Unix timestamps into dates, and a date into Unix time."""

    def __init__(self, **properties):
        super().__init__(**properties)
        state.set_control_attr(self.id_box, "inputmode", "numeric")
        state.set_control_attr(self.dt_box, "type", "datetime-local")
        self.id_box.add_event_handler("change", self._run)
        self.dt_box.add_event_handler("change", self._run)
        self._run()

    def _run(self, **event_args):
        s = re.sub(r"\D", "", self.id_box.text or "")
        out = []
        if s:
            if 15 <= len(s) <= 20:
                tw, dc = gadget_kit.snowflake_ms(s)
                out.append({"label": "As an X / Twitter post ID", "big": _fmt(tw) or ["not valid"]})
                out.append({"label": "As a Discord ID", "big": _fmt(dc) or ["not valid"]})
                out.append({"label": "Which one?", "text": "Use the one that matches where the ID came from. The other reading is meaningless."})
            elif len(s) in (10, 13):
                ms = int(s) * 1000 if len(s) == 10 else int(s)
                out.append({"label": "Unix time (%s)" % ("seconds" if len(s) == 10 else "milliseconds"), "big": _fmt(ms) or ["not valid"]})
            else:
                out.append({"label": "Hmm", "text": "That's %d digits. Snowflake IDs have 15 to 20 digits; Unix times have 10 (seconds) or 13 (milliseconds)." % len(s)})
        dt = self.dt_box.text or ""
        if dt:
            ms = window.Date.parse(dt + ":00Z")
            if not window.isNaN(ms):
                out.append({"label": dt.replace("T", " ") + " UTC as Unix time", "big": ["%d s · %d ms" % (int(ms // 1000), int(ms))]})
        self.out_panel.items = out or [{"label": "Result", "text": "Paste an ID or a timestamp."}]
