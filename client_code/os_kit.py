"""Osinty's shared client helpers (the old window.OS): tiny Markdown, XP celebrations, rank badges, lead kinds,
case-file sources, dates, copy. Drawing engines live in theme/assets/os-kit.js (window.OS) and are reached from here.

    os_kit.md(text)              **bold**, *italic*, `code` -> safe HTML (escapes first; content strings use only these)
    os_kit.paras(list)           paragraphs of md() in a <div class="os-md">
    os_kit.celebrate(reply)      +XP stamp, "Badge unlocked" toasts, the promotion dialog (replies that award XP)
    os_kit.shield(level)         the rank badge SVG (Components/Shield shows it)
"""
import re

import anvil
import anvil.js
from anvil.js import window

from . import state

KIND_ICON = {"person": "user", "username": "fingerprint", "email": "mail", "phone": "chat", "address": "home", "place": "pin",
             "domain": "globe", "organisation": "briefcase", "vehicle": "target", "image": "image", "event": "calendar",
             "document": "book", "note": "edit"}
SRC_ICON = {"web": "search", "social": "users", "records": "book", "whois": "globe", "archive": "clock", "image": "camera"}
STATUS = [("open", "Open", ""), ("cold", "Cold", "muted"), ("closed", "Closed", "good")]
MONTHS_LONG = state.MONTHS_LONG


def kind_label(kind):
    return "Organisation" if kind == "organisation" else (kind or "").capitalize()


def esc(text):
    return str(window.UI.esc(text if text is not None else ""))


def md(text):
    s = esc(text or "")
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(^|[^*])\*([^*\n]+)\*", r"\1<em>\2</em>", s)
    return s.replace("\n", "<br>")


def paras(items):
    return '<div class="os-md">' + "".join("<p>" + md(p) + "</p>" for p in (items or [])) + "</div>"


def shield(level):
    return str(window.OS.shield(level or 1))


def long_date(iso):
    """'2026-11-02...' -> '2 November 2026'."""
    if not iso:
        return ""
    y, m, d = iso[:10].split("-")
    return "%d %s %s" % (int(d), MONTHS_LONG[int(m) - 1], y)


def today_long():
    d = window.Date()
    return "%s %d %s %d" % (["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][d.getDay()],
                            d.getDate(), MONTHS_LONG[d.getMonth()], d.getFullYear())


def copy(text, message="Copied."):
    window.OS.copy(text, lambda: state.toast(message, "ok"),
                   lambda: state.toast("Copy didn't work here: select the text instead.", "error"))


def celebrate(reply):
    """XP gained, a promotion, new badges: the stamp, toasts, a promotion card."""
    if not reply:
        return
    if (reply.get("xp_gained") or 0) > 0:
        window.OS.xpPop(reply["xp_gained"])
    for i, b in enumerate(reply.get("badges") or []):
        window.setTimeout(lambda name=b["name"]: state.toast("Badge unlocked: " + name, "ok"), 700 + i * 500)
    if reply.get("rank_up") and reply.get("me"):
        window.setTimeout(anvil.js.report_exceptions(lambda: _promotion(reply)), 900)


def _promotion(reply):
    from .Dialogs.Promotion import Promotion
    anvil.alert(Promotion(reply=reply), buttons=[], role="app-dialog", dismissible=True)
