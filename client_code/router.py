"""Page addresses: #name/arg1/arg2 -> a page Form (open_form), with sign-in rules. The addresses are the old app's
(links people shared keep working): #academy/<lesson>, #cases/<case>, #casebook/<id>/<tab>, #kit/<gadget>, #admin/<tab>.

Links in templates are plain <a href="#home">; code calls router.go("cases", case_id).

    PAGES[name] = (who may open it, browser-tab title)   who: None = anyone, "guest" = signed out only, "user", "admin"
    NAV = the main menu (header; the phone tab bar shows the first four + Dossier): (page, label, icon).
New page: add it to PAGES, to _form() and (if it belongs in the menu) to NAV.
"""
import anvil
import anvil.js
from anvil.js import window

from . import state

PAGES = {
    "landing": (None, "Learn OSINT like a private investigator"),
    "auth": ("guest", "Sign in"),
    "home": ("user", "The Office"),
    "academy": ("user", "Academy"),
    "cases": ("user", "Case files"),
    "casebook": ("user", "Casebook"),
    "kit": ("user", "Field Kit"),
    "profile": ("user", "Your dossier"),
    "admin": ("admin", "Admin"),
}
NAV = [("home", "Office", "hat"), ("academy", "Academy", "book"), ("cases", "Cases", "folder"),
       ("casebook", "Casebook", "board"), ("kit", "Kit", "tool")]
APP_NAME = "Osinty"
_r: dict = {"after": "", "listening": False, "page": None, "form": None}


def _form(name, args):
    """The page's Form class (imported when first needed, so start-up stays quick). Pages with a list and a detail
    view (academy, cases, casebook) open a different Form when the address names one item."""
    if name == "landing":
        from .Pages.Landing import Landing
        return Landing
    if name == "auth":
        from .Pages.Auth import Auth
        return Auth
    if name == "home":
        from .Pages.Home import Home
        return Home
    if name == "academy":
        if args:
            from .Pages.Lesson import Lesson
            return Lesson
        from .Pages.Academy import Academy
        return Academy
    if name == "cases":
        if args:
            from .Pages.CaseDesk import CaseDesk
            return CaseDesk
        from .Pages.Cases import Cases
        return Cases
    if name == "casebook":
        if args:
            from .Pages.Investigation import Investigation
            return Investigation
        from .Pages.Casebook import Casebook
        return Casebook
    if name == "kit":
        from .Pages.Kit import Kit
        return Kit
    if name == "profile":
        from .Pages.Profile import Profile
        return Profile
    from .Pages.Admin import Admin
    return Admin


def parse(hash_text):
    h = (hash_text or "").lstrip("#").lstrip("!").lstrip("/").split("?")[0]
    parts = [window.decodeURIComponent(p) for p in h.split("/") if p]
    return (parts[0] if parts else ""), parts[1:]


def href(name, *args):
    """'#name/arg1/arg2' with every part URL-encoded (row ids contain brackets and commas)."""
    return "#" + "/".join([name] + [window.encodeURIComponent(str(a)) for a in args if a not in (None, "")])


def home_page():
    return "home" if state.me() else "landing"


def current():
    """The page name now open ("home", "cases" ...)."""
    return _r["page"]


def set_title(text):
    """A page that knows a better tab title (a lesson's or a case's name)."""
    window.document.title = text + " · " + APP_NAME


def show():
    """Open the page for the current address."""
    name, args = parse(window.location.hash)
    if name not in PAGES:
        name, args = home_page(), []
        if (window.location.hash or "#") != "#":
            replace(name)
    who = PAGES[name][0]
    if who == "guest" and state.me():
        name, args = "home", []
        replace(name)
    elif who in ("user", "admin") and not state.me():
        _r["after"] = window.location.hash
        name, args = "auth", []
    elif who == "admin" and not state.is_admin():
        state.toast("That page is for admins only.", "error")
        name, args = "home", []
        replace(name)
    window.document.title = PAGES[name][1] + " · " + APP_NAME
    window.UI_READY = False
    old = _r["form"]
    if old is not None and hasattr(old, "leave"):
        old.leave()  # pages with engines or timers tidy up (the corkboard, the EXIF photo)
    _r["page"] = name
    page = _form(name, args)(args=args)
    _r["form"] = page
    anvil.open_form(page)
    shell = getattr(page, "layout", None)
    if shell is not None and hasattr(shell, "refresh"):
        shell.refresh(name)  # Anvil reuses the layout between pages: tell it who is signed in and which page is open
    window.scrollTo(0, 0)
    window.UI_READY = True  # tests and screenshots wait for this


def go(name, *args):
    """Go to a page. Same address again = reload the page."""
    target = href(name, *args)
    if window.location.hash == target:
        show()
    else:
        window.location.hash = target


def replace(name, *args):
    """Change the address without opening anything (a page that switches its own view)."""
    window.history.replaceState(None, "", href(name, *args))


def after_sign_in():
    """Where to go once someone signs in: the page they were heading for, or home."""
    target = _r["after"]
    _r["after"] = ""
    if target and target != window.location.hash:
        window.location.hash = target
    else:
        go("home")


def remember_after(target):
    _r["after"] = target


def _on_hash(event):
    show()


def start():
    if not _r["listening"]:
        window.addEventListener("hashchange", anvil.js.report_exceptions(_on_hash))
        _r["listening"] = True
    show()
