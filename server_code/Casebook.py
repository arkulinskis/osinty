"""Casebook: a person's own investigations. Only the owner (or nobody) ever sees them.

investigations -> leads (corkboard pins: a person, username, email, place... with a source and an
Admiralty grade) -> links (the red strings between two leads). The checklist walks the intelligence
cycle and the legal/ethical checks.
"""
import re

import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import Agents

STATUSES = ("open", "cold", "closed")
KINDS = ("person", "username", "email", "phone", "address", "place", "domain", "organisation", "vehicle", "image", "event", "document", "note")
GRADE = re.compile(r"^[A-F][1-6]$")
CHECKLIST = [
    ("purpose", "The purpose is legitimate and written down"),
    ("law", "I checked which laws apply (mine, the client's, the subject's)"),
    ("question", "The question is one sentence I could answer with a fact"),
    ("opsec", "I'm working from a separate, logged-out research profile"),
    ("collect", "I've searched at least three different kinds of source"),
    ("capture", "Key pages are archived and screenshotted with URL and time"),
    ("verify", "Key facts are confirmed by two independent sources"),
    ("grade", "Every lead has an Admiralty grade"),
    ("alternative", "I wrote down the best alternative explanation and tested it"),
    ("report", "The report leads with the answer (BLUF) and separates facts from assessments"),
]
MAX_INVESTIGATIONS = 50
MAX_LEADS = 120
BOARD_W, BOARD_H = 1400, 900


def _own(inv_id, me):
    inv = C.row_by_id(app_tables.investigations, inv_id)
    if inv is None or inv["owner"] != me:
        return None
    return inv


def _own_lead(lead_id, me):
    lead = C.row_by_id(app_tables.leads, lead_id)
    if lead is None or lead["investigation"] is None or lead["investigation"]["owner"] != me:
        return None
    return lead


def _inv(inv, counts=True):
    out = {"id": inv.get_id(), "title": inv["title"], "subject": inv["subject"] or "", "objective": inv["objective"] or "",
           "status": inv["status"] or "open", "created": C.iso(inv["created"]), "updated": C.iso(inv["updated"]),
           "checklist": dict(inv["checklist"] or {})}
    if counts:
        out["leads"] = len(app_tables.leads.search(investigation=inv))
        out["links"] = len(app_tables.links.search(investigation=inv))
    return out


def _lead(lead):
    return {"id": lead.get_id(), "kind": lead["kind"], "value": lead["value"], "note": lead["note"] or "", "source": lead["source"] or "",
            "grade": lead["grade"] or "", "when": lead["when"] or "", "x": int(lead["x"] or 0), "y": int(lead["y"] or 0),
            "created": C.iso(lead["created"])}


def _link(link):
    return {"id": link.get_id(), "a": link["a"].get_id(), "b": link["b"].get_id(), "label": link["label"] or ""}


def _clean_lead(data):
    data = data if isinstance(data, dict) else {}
    kind = data.get("kind") if data.get("kind") in KINDS else "note"
    value = C.text(data.get("value"), 160)
    grade = C.text(data.get("grade"), 2).upper()
    out = {"kind": kind, "value": value, "note": C.text(data.get("note"), 1500, multiline=True),
           "source": C.text(data.get("source"), 400), "grade": grade if GRADE.match(grade) else "",
           "when": C.text(data.get("when"), 40)}
    return out


def _touch(inv):
    inv["updated"] = C.now()


def _free_spot(inv):
    n = len(app_tables.leads.search(investigation=inv))
    col, row = n % 5, (n // 5) % 6
    return 40 + col * 250 + (row % 2) * 60, 40 + row * 140


@anvil.server.callable(require_user=True)
def list_investigations():
    me = C.require_user()
    rows = sorted(app_tables.investigations.search(owner=me), key=lambda r: r["updated"] or r["created"], reverse=True)
    return {"items": [_inv(r) for r in rows], "checklist": [{"id": k, "text": t} for k, t in CHECKLIST]}


@anvil.server.callable(require_user=True)
def create_investigation(title, subject="", objective=""):
    me = C.require_user()
    title = C.text(title, 100)
    if len(title) < 2:
        return C.fail("Give the investigation a title (at least 2 characters).")
    if len(app_tables.investigations.search(owner=me)) >= MAX_INVESTIGATIONS:
        return C.fail("You have %d investigations. Delete a few old ones first." % MAX_INVESTIGATIONS)
    if C.rate_limited("create_investigation", 20, 3600):
        return C.fail("That's a lot of new files in an hour. Try again later.")
    inv = app_tables.investigations.add_row(owner=me, title=title, subject=C.text(subject, 160), objective=C.text(objective, 600, multiline=True),
                                            status="open", checklist={}, created=C.now(), updated=C.now(), is_demo=False)
    Agents.touch(me)
    return C.ok(investigation=_inv(inv))


SAMPLE = {
    "title": "Training file: the Lumenhaus network",
    "subject": "Who runs lumenhaus-deals.example?",
    "objective": "Establish the age of the shop, whether it belongs to a network of fake shops, and who might be behind it. For the client's report to police and the bank.",
    "leads": [
        ("domain", "lumenhaus-deals.example", "Fake lamp shop, 'trusted since 1998'. Customers paid, nothing arrived.", "Client", "B2", "", 60, 60),
        ("event", "Domain registered 2 Sep 2026", "Contradicts 'since 1998'. Privacy service on.", "WHOIS lookup", "A1", "2026-09-02", 330, 30),
        ("document", "Tracking ID LX-447821", "In the page source. Pivot!", "View source", "A1", "", 120, 240),
        ("domain", "nordic-sofa-outlet.example", "Same tracking ID. 212 bad reviews, vanished March 2025.", "Source-code search", "B2", "", 420, 230),
        ("organisation", "VK Media Solutions SIA", "Historical WHOIS of the sofa shop (Mar 2024). Liquidated Nov 2025.", "Historical WHOIS", "B3", "2024-03-12", 720, 180),
        ("person", "Velta Krūmiņa", "Director of VK Media; also on 2 other liquidated firms. Do NOT contact.", "Business register", "B3", "", 760, 380),
    ],
    "links": [(0, 1, "registered"), (0, 2, "uses"), (2, 3, "shared ID"), (3, 4, "registrant 2024"), (4, 5, "director")],
    "checklist": {"purpose": True, "law": True, "question": True, "opsec": True},
}


@anvil.server.callable(require_user=True)
def create_sample_investigation():
    """A filled-in training investigation, so the corkboard and report make sense at once."""
    me = C.require_user()
    if len(app_tables.investigations.search(owner=me)) >= MAX_INVESTIGATIONS:
        return C.fail("You have %d investigations. Delete a few old ones first." % MAX_INVESTIGATIONS)
    if C.rate_limited("create_investigation", 20, 3600):
        return C.fail("That's a lot of new files in an hour. Try again later.")
    inv = app_tables.investigations.add_row(owner=me, title=SAMPLE["title"], subject=SAMPLE["subject"], objective=SAMPLE["objective"],
                                            status="open", checklist=dict(SAMPLE["checklist"]), created=C.now(), updated=C.now(), is_demo=False)
    leads = []
    for kind, value, note, source, grade, when, x, y in SAMPLE["leads"]:
        leads.append(app_tables.leads.add_row(investigation=inv, kind=kind, value=value, note=note, source=source, grade=grade,
                                              when=when, x=x, y=y, created=C.now()))
    for a, b, label in SAMPLE["links"]:
        app_tables.links.add_row(investigation=inv, a=leads[a], b=leads[b], label=label, created=C.now())
    Agents.touch(me)
    return C.ok(investigation=_inv(inv))


@anvil.server.callable(require_user=True)
def get_investigation(inv_id):
    me = C.require_user()
    inv = _own(inv_id, me)
    if inv is None:
        return C.fail("That investigation doesn't exist, or isn't yours.")
    leads = sorted(app_tables.leads.search(investigation=inv), key=lambda r: r["created"])
    links = list(app_tables.links.search(investigation=inv))
    return C.ok(investigation=_inv(inv, counts=False), leads=[_lead(x) for x in leads], links=[_link(x) for x in links],
                checklist=[{"id": k, "text": t} for k, t in CHECKLIST], kinds=list(KINDS),
                board={"w": BOARD_W, "h": BOARD_H})


@anvil.server.callable(require_user=True)
def update_investigation(inv_id, data):
    me = C.require_user()
    inv = _own(inv_id, me)
    if inv is None:
        return C.fail("That investigation doesn't exist, or isn't yours.")
    data = data if isinstance(data, dict) else {}
    changes = {}
    if "title" in data:
        title = C.text(data["title"], 100)
        if len(title) < 2:
            return C.fail("Give the investigation a title (at least 2 characters).")
        changes["title"] = title
    if "subject" in data:
        changes["subject"] = C.text(data["subject"], 160)
    if "objective" in data:
        changes["objective"] = C.text(data["objective"], 600, multiline=True)
    if "status" in data:
        if data["status"] not in STATUSES:
            return C.fail("Unknown status.")
        changes["status"] = data["status"]
    changes["updated"] = C.now()
    inv.update(**changes)
    return C.ok(investigation=_inv(inv))


@anvil.server.callable(require_user=True)
def set_checklist(inv_id, key, flag):
    me = C.require_user()
    inv = _own(inv_id, me)
    if inv is None:
        return C.fail("That investigation doesn't exist, or isn't yours.")
    if key not in dict(CHECKLIST):
        return C.fail("Unknown checklist item.")
    cl = dict(inv["checklist"] or {})
    cl[key] = bool(flag)
    inv.update(checklist=cl, updated=C.now())
    return C.ok(checklist=cl)


@anvil.server.callable(require_user=True)
def delete_investigation(inv_id):
    me = C.require_user()
    inv = _own(inv_id, me)
    if inv is None:
        return C.ok()
    for link in app_tables.links.search(investigation=inv):
        link.delete()
    for lead in app_tables.leads.search(investigation=inv):
        lead.delete()
    inv.delete()
    return C.ok()


@anvil.server.callable(require_user=True)
def add_lead(inv_id, data):
    me = C.require_user()
    inv = _own(inv_id, me)
    if inv is None:
        return C.fail("That investigation doesn't exist, or isn't yours.")
    d = _clean_lead(data)
    if len(d["value"]) < 1:
        return C.fail("A lead needs a value (a name, a username, an address...).")
    if len(app_tables.leads.search(investigation=inv)) >= MAX_LEADS:
        return C.fail("This board is full (%d leads). Close the case or start a new file." % MAX_LEADS)
    if C.rate_limited("add_lead", 200, 3600):
        return C.fail("That's a lot of leads in one hour. Take a break and try again.")
    before = Agents.snapshot(me)
    x, y = _free_spot(inv)
    lead = app_tables.leads.add_row(investigation=inv, x=x, y=y, created=C.now(), **d)
    _touch(inv)
    Agents.touch(me)
    out = C.ok(lead=_lead(lead))
    out.update(Agents.changes(me, before))
    return out


@anvil.server.callable(require_user=True)
def update_lead(lead_id, data):
    me = C.require_user()
    lead = _own_lead(lead_id, me)
    if lead is None:
        return C.fail("That lead doesn't exist, or isn't yours.")
    d = _clean_lead(data)
    if len(d["value"]) < 1:
        return C.fail("A lead needs a value.")
    lead.update(**d)
    _touch(lead["investigation"])
    return C.ok(lead=_lead(lead))


@anvil.server.callable(require_user=True)
def move_lead(lead_id, x, y):
    me = C.require_user()
    lead = _own_lead(lead_id, me)
    if lead is None:
        return C.fail("That lead doesn't exist, or isn't yours.")
    try:
        x, y = int(x), int(y)
    except (TypeError, ValueError):
        return C.fail("Bad position.")
    lead.update(x=max(0, min(BOARD_W - 180, x)), y=max(0, min(BOARD_H - 90, y)))
    return C.ok()


@anvil.server.callable(require_user=True)
def delete_lead(lead_id):
    me = C.require_user()
    lead = _own_lead(lead_id, me)
    if lead is None:
        return C.ok()
    for link in list(app_tables.links.search(a=lead)) + list(app_tables.links.search(b=lead)):
        link.delete()
    inv = lead["investigation"]
    lead.delete()
    _touch(inv)
    return C.ok()


@anvil.server.callable(require_user=True)
def add_link(inv_id, a_id, b_id, label=""):
    me = C.require_user()
    inv = _own(inv_id, me)
    if inv is None:
        return C.fail("That investigation doesn't exist, or isn't yours.")
    a, b = _own_lead(a_id, me), _own_lead(b_id, me)
    if a is None or b is None or a["investigation"] != inv or b["investigation"] != inv:
        return C.fail("Pick two leads from this board.")
    if a == b:
        return C.fail("A lead can't be connected to itself.")
    for link in app_tables.links.search(investigation=inv):
        if {link["a"], link["b"]} == {a, b}:
            return C.fail("Those two are already connected.")
    before = Agents.snapshot(me)
    link = app_tables.links.add_row(investigation=inv, a=a, b=b, label=C.text(label, 40), created=C.now())
    _touch(inv)
    out = C.ok(link=_link(link))
    out.update(Agents.changes(me, before))
    return out


@anvil.server.callable(require_user=True)
def delete_link(link_id):
    me = C.require_user()
    link = C.row_by_id(app_tables.links, link_id)
    if link is None:
        return C.ok()
    if link["investigation"] is None or link["investigation"]["owner"] != me:
        return C.fail("That connection isn't yours.")
    link.delete()
    return C.ok()
