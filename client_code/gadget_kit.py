"""The Field Kit gadgets' logic: usernames, email formats, dorks, ID/time decoding, the Admiralty advice.
Gadgets/* show it."""
import re

from anvil.js import window


def slug(s):
    """Lower case, accents dropped (José -> jose), letters and digits only."""
    s = str(window.OS.fold(s or ""))
    return re.sub(r"[^a-z0-9]", "", s)


def _unique(items):
    out = []
    for x in items:
        if x and x not in out:
            out.append(x)
    return out


def usernames(first, last, extra):
    f, l, x = slug(first), slug(last), slug(extra)
    if not f and not l:
        return []
    fi, li = f[:1], l[:1]
    if f and l:
        base = [f + l, f + "." + l, f + "_" + l, f + "-" + l, fi + l, fi + "." + l, fi + "_" + l, f + li, l + f, l + "." + f,
                l + fi, f + l[:4], f[:4] + l[:4], fi + li]
    else:
        base = [f or l]
    out = list(base)
    if x:
        for b in base[:8]:
            out += [b + x, b + "_" + x]
    if x and len(x) == 4:
        for b in base[:4]:
            out.append(b + x[2:])
    return _unique(out)


def emails(first, last, domain):
    f, l = slug(first), slug(last)
    d = re.sub(r"[^a-z0-9.-]", "", (domain or "").strip().lower().lstrip("@"))
    if not f or not d:
        return []
    fi, li = f[:1], l[:1]
    names = [f + "." + l, fi + l, f, f + l, f + "_" + l, fi + "." + l, f + li, l + "." + f, l + fi, l, f + "-" + l, fi + li] if l else [f]
    return _unique([n + "@" + d for n in names])


def dork(v):
    """v = the dork builder's fields (exact, all, any, not, site, type, intitle, inurl, after, before)."""
    def words(s):
        return [w for w in (s or "").strip().split() if w]
    out = []
    exact = (v.get("exact") or "").strip().replace('"', "")
    if exact:
        out.append('"%s"' % exact)
    out += words(v.get("all"))
    anyw = words(v.get("any"))
    if anyw:
        out.append("(" + " OR ".join(anyw) + ")" if len(anyw) > 1 else anyw[0])
    out += ["-" + w.lstrip("-") for w in words(v.get("not"))]
    if (v.get("site") or "").strip():
        out.append("site:" + v["site"].strip())
    if v.get("type"):
        out.append("filetype:" + v["type"])
    it = (v.get("intitle") or "").strip()
    if it:
        out.append("intitle:" + ('"%s"' % it if re.search(r"\s", it) else it))
    if (v.get("inurl") or "").strip():
        out.append("inurl:" + v["inurl"].strip())
    if v.get("after"):
        out.append("after:" + v["after"])
    if v.get("before"):
        out.append("before:" + v["before"])
    return " ".join(out)


TWITTER_EPOCH, DISCORD_EPOCH = 1288834974657, 1420070400000


def snowflake_ms(digits):
    """(twitter_ms, discord_ms) for a snowflake ID: its first bits are the creation time in milliseconds."""
    t = int(digits) >> 22
    return t + TWITTER_EPOCH, t + DISCORD_EPOCH


def grade_advice(rel, cred):
    n = int(cred)
    if n <= 2 and rel in "ABC":
        return "Strong enough to state as a finding, with the source cited."
    if n <= 3:
        return "Report it as an assessment (\"likely\", \"possibly\") and look for a second, independent source."
    return "Treat as unconfirmed. Don't base conclusions on it; flag it and keep digging."


REL_HELP = {"A": "A proven, authoritative source: an official register, a court record.",
            "B": "Generally right, minor doubts: an established newspaper, a well-run company site.",
            "C": "Has been right before, but you have doubts: a known blogger, a review site.",
            "D": "Often wrong or biased: a tabloid, an anonymous aggregator.",
            "E": "Known to be wrong, or a suspected liar.",
            "F": "A new source you can't assess yet: an anonymous account, a first-time forum poster."}
