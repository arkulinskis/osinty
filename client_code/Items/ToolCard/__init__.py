from anvil import *

from ._anvil_designer import ToolCardTemplate
from ... import os_data, state

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def month_label(ym):
    """'2026-11' -> 'Nov 2026'."""
    try:
        y, m = str(ym)[:7].split("-")
        return "%s %s" % (MONTHS[int(m) - 1], y)
    except Exception:
        return ""


class ToolCard(ToolCardTemplate):
    """One real tool in the library, with its tip and a star (save to my kit). item = a tool + saved + host + link
    (the last admin link check for this tool: {state: ok|blocked|down, when} or None).
    Shows "Checked <month>", a Paywalled / Unmaintained / Frozen stamp with its note, and a warning when the last
    link check couldn't reach the site."""

    def __init__(self, **properties):
        super().__init__(**properties)
        t, n = self.item, self.dom_nodes
        n["cat"].textContent = os_data.CATS.get(t["cat"], "")
        n["name"].textContent = t["name"]
        n["what"].textContent = t["what"]
        n["tip"].textContent = t["tip"]
        n["open_sr"].textContent = " " + t["name"] + " (opens a new tab)"
        state.set_attr(self.open_link, "href", t["url"])
        n["cost"].className = "ui-badge" + (" good" if t["cost"] == "Free" else " warn" if t["cost"].startswith("Paid") else "")
        n["cost"].textContent = t["cost"]
        status = os_data.STATUS.get(t.get("status") or "")
        n["status"].textContent = status or ""
        n["status"].style.display = "" if status else "none"
        n["note"].textContent = t.get("note") or ""
        n["note"].style.display = "" if t.get("note") else "none"
        link = t.get("link") or {}
        down = link.get("state") == "down"
        when = month_label(link.get("when")) if link.get("when") and link.get("state") == "ok" else ""
        if down:
            n["checked"].textContent = "Link didn't answer at the last check (%s)" % month_label(link.get("when"))
        else:
            n["checked"].textContent = "Checked " + (when or month_label(t.get("checked")) or "recently")
        n["checked_icon"].className = "ic " + ("ic-info" if down else "ic-check")
        n["article"].classList.toggle("is-down", down)
        on = bool(t.get("saved"))
        self.star_button.text = ("Remove %s from my kit" if on else "Save %s to my kit") % t["name"]
        self.star_button.role = ["btn", "btn-ghost", "btn-icon", "ic-star", "kt-star"] + (["on"] if on else [])
        state.set_control_attr(self.star_button, "aria-pressed", "true" if on else "false")

    @handle("star_button", "click")
    def star_button_click(self, **event_args):
        self.item["host"].star(self.item["id"])
