"""Osinty's client-side data: the Field Kit library of real tools (TOOLS, in CATS), the in-browser gadgets
(GADGETS, #kit/<id>) and the Admiralty grading tables (REL, CRED). Lessons name tool ids from here
(server_code/lessons_content.py); tools/testing/test_server.py checks every id exists.
Every tool has `checked` (YYYY-MM, when a person last checked it still works as described) and, where it applies,
`status` (paywalled | unmaintained | frozen) + `note` (shown as a stamp on the card). Admin -> Training -> "Check tool
links" pings every url (Admin.admin_check_tools) and the cards show the result."""

STATUS = {"paywalled": "Paywalled", "unmaintained": "Unmaintained", "frozen": "Frozen"}

CATS = {
    "search": "Search engines",
    "archive": "Archives & capture",
    "people": "People & usernames",
    "images": "Images & video",
    "geo": "Maps & geolocation",
    "companies": "Companies & money",
    "domains": "Domains & infrastructure",
    "transport": "Planes & ships",
    "method": "Method & community",
}

TOOLS = [
    {"id": "googleadvanced", "name": "Google Advanced Search", "cat": "search", "cost": "Free", "url": "https://www.google.com/advanced_search", "what": "A form for operators: exact phrases, sites, file types, dates.", "tip": "Learn the operators here, then type them directly.", "checked": "2026-11"},
    {"id": "bing", "name": "Bing", "cat": "search", "cost": "Free", "url": "https://www.bing.com", "what": "A different index, plus operators like ip: and inbody:.", "tip": "Repeat every important dork here.", "checked": "2026-11"},
    {"id": "yandex", "name": "Yandex Images", "cat": "images", "cost": "Free", "url": "https://yandex.com/images/", "what": "Reverse image search known for faces, buildings and landmarks.", "tip": "Crop to the face or the building before uploading.", "checked": "2026-11"},
    {"id": "googlelens", "name": "Google Lens", "cat": "images", "cost": "Free", "url": "https://lens.google/", "what": "Reverse image search for objects, products, places and text.", "tip": "Select just one region of the image for sharper matches.", "checked": "2026-11"},
    {"id": "bingvisual", "name": "Bing Visual Search", "cat": "images", "cost": "Free", "url": "https://www.bing.com/visualsearch", "what": "Microsoft's reverse image search, with different results again.", "tip": "Good for finding the same photo at other sizes.", "checked": "2026-11"},
    {"id": "tineye", "name": "TinEye", "cat": "images", "cost": "Freemium", "url": "https://tineye.com", "what": "Finds exact copies of an image and sorts them by date.", "tip": "Sort by \"Oldest\" to find the source.", "checked": "2026-11"},
    {"id": "invid", "name": "InVID-WeVerify plugin", "cat": "images", "cost": "Free", "url": "https://www.invid-project.eu/tools-and-services/invid-verification-plugin/", "what": "Browser plugin to split videos into keyframes and verify them.", "tip": "Reverse-search several keyframes, not just the first.", "checked": "2026-11"},
    {"id": "exiftool", "name": "ExifTool", "cat": "images", "cost": "Free", "url": "https://exiftool.org", "what": "The reference tool for reading metadata in photos, videos and documents.", "tip": "Run it on PDFs and Office files too: authors leak.", "checked": "2026-11"},
    {"id": "forensically", "name": "Forensically", "cat": "images", "cost": "Free", "url": "https://29a.ch/photo-forensics/", "what": "In-browser photo forensics: clone detection, error level analysis, metadata.", "tip": "Edits leave traces; but read the help before concluding anything.", "checked": "2026-11"},
    {"id": "wayback", "name": "Wayback Machine", "cat": "archive", "cost": "Free", "url": "https://web.archive.org", "what": "Hundreds of billions of archived web pages since 1996, and \"Save Page Now\".", "tip": "Type a domain followed by /* to list every URL it knows.", "checked": "2026-11"},
    {"id": "archivetoday", "name": "archive.today", "cat": "archive", "cost": "Free", "url": "https://archive.ph", "what": "On-demand page captures, including some sites other archivers can't reach.", "tip": "Capture key pages yourself before they change.", "checked": "2026-11"},
    {"id": "hunchly", "name": "Hunchly", "cat": "archive", "cost": "Paid", "url": "https://www.hunch.ly", "what": "Captures every page you visit during a case, with hashes and notes.", "tip": "The professional way to keep a chain of custody.", "checked": "2026-11"},
    {"id": "whatsmyname", "name": "WhatsMyName", "cat": "people", "cost": "Free", "status": "frozen", "note": "Archived by its creator in November 2026: the site still runs, but nobody updates its site checks, so treat a miss as unknown.", "url": "https://whatsmyname.app", "what": "Checks a username on hundreds of websites at once.", "tip": "Confirm every hit with a shared detail; namesakes abound.", "checked": "2026-11"},
    {"id": "sherlock", "name": "Sherlock", "cat": "people", "cost": "Free", "url": "https://github.com/sherlock-project/sherlock", "what": "Open-source command-line username search across many sites.", "tip": "Great for batches of username variants.", "checked": "2026-11"},
    {"id": "maigret", "name": "Maigret", "cat": "people", "cost": "Free", "url": "https://github.com/soxoj/maigret", "what": "Open-source username search across thousands of sites, with a report of what each profile shows.", "tip": "The actively maintained successor to Sherlock-style checkers; still verify every hit.", "checked": "2026-11"},
    {"id": "hibp", "name": "Have I Been Pwned", "cat": "people", "cost": "Free", "url": "https://haveibeenpwned.com", "what": "Shows which known data breaches an email appears in (never the data).", "tip": "Breach names hint at which sites someone used.", "checked": "2026-11"},
    {"id": "courtlistener", "name": "CourtListener", "cat": "people", "cost": "Free", "url": "https://www.courtlistener.com", "what": "Free search of US court opinions and many federal dockets.", "tip": "Search names with and without middle initials.", "checked": "2026-11"},
    {"id": "canlii", "name": "CanLII", "cat": "people", "cost": "Free", "url": "https://www.canlii.org", "what": "Canadian court and tribunal decisions, free.", "tip": "Use quotes and the province filter.", "checked": "2026-11"},
    {"id": "opencorporates", "name": "OpenCorporates", "cat": "companies", "cost": "Freemium", "url": "https://opencorporates.com", "what": "Company records from 100+ jurisdictions in one search.", "tip": "Search officers (people), not just companies.", "checked": "2026-11"},
    {"id": "companieshouse", "name": "UK Companies House", "cat": "companies", "cost": "Free", "url": "https://find-and-update.company-information.service.gov.uk/", "what": "Every UK company: directors, filings, addresses, history.", "tip": "Click a director to see all their appointments.", "checked": "2026-11"},
    {"id": "edgar", "name": "SEC EDGAR", "cat": "companies", "cost": "Free", "url": "https://www.sec.gov/edgar/search/", "what": "Filings of US public companies and their insiders.", "tip": "Full-text search finds names buried in filings.", "checked": "2026-11"},
    {"id": "offshoreleaks", "name": "ICIJ Offshore Leaks", "cat": "companies", "cost": "Free", "url": "https://offshoreleaks.icij.org", "what": "Entities and people from the Panama, Paradise and Pandora papers.", "tip": "Search addresses too: offshore agents reuse them.", "checked": "2026-11"},
    {"id": "opensanctions", "name": "OpenSanctions", "cat": "companies", "cost": "Freemium", "url": "https://www.opensanctions.org", "what": "Sanctions lists, politically exposed persons and watchlists combined.", "tip": "A must for due-diligence work.", "checked": "2026-11"},
    {"id": "viewdns", "name": "ViewDNS.info", "cat": "domains", "cost": "Freemium", "url": "https://viewdns.info", "what": "WHOIS, reverse IP, reverse WHOIS, DNS history and more.", "tip": "Reverse IP shows other sites on the same server.", "checked": "2026-11"},
    {"id": "crtsh", "name": "crt.sh", "cat": "domains", "cost": "Free", "url": "https://crt.sh", "what": "Certificate-transparency logs: every TLS certificate issued for a domain.", "tip": "Search %.domain.com to uncover hidden subdomains.", "checked": "2026-11"},
    {"id": "dnsdumpster", "name": "DNSDumpster", "cat": "domains", "cost": "Freemium", "url": "https://dnsdumpster.com", "what": "Maps a domain's DNS records and hosts.", "tip": "Shared mail servers can link organisations.", "checked": "2026-11"},
    {"id": "urlscan", "name": "urlscan.io", "cat": "domains", "cost": "Freemium", "url": "https://urlscan.io", "what": "Loads a page in a sandbox and shows everything it contacts.", "tip": "Search past scans for a tracking ID or IP.", "checked": "2026-11"},
    {"id": "shodan", "name": "Shodan", "cat": "domains", "cost": "Freemium", "url": "https://www.shodan.io", "what": "A search engine for internet-connected devices and servers.", "tip": "Look, never touch: logging into devices is unauthorised access.", "checked": "2026-11"},
    {"id": "googleearth", "name": "Google Earth", "cat": "geo", "cost": "Free", "url": "https://earth.google.com", "what": "Satellite imagery, 3D terrain and historical imagery (desktop).", "tip": "The historical imagery slider dates construction.", "checked": "2026-11"},
    {"id": "streetview", "name": "Google Street View", "cat": "geo", "cost": "Free", "url": "https://www.google.com/maps", "what": "Stand where the photographer stood.", "tip": "Check older capture dates when the scene changed.", "checked": "2026-11"},
    {"id": "mapillary", "name": "Mapillary", "cat": "geo", "cost": "Free", "url": "https://www.mapillary.com", "what": "Crowd-sourced street-level photos, often where Street View isn't.", "tip": "Great for back roads and newer areas.", "checked": "2026-11"},
    {"id": "overpass", "name": "Overpass Turbo", "cat": "geo", "cost": "Free", "url": "https://overpass-turbo.eu", "what": "Query OpenStreetMap: \"every church within 200 m of a river bridge\".", "tip": "Turns a vague scene into a short list of candidates.", "checked": "2026-11"},
    {"id": "suncalc", "name": "SunCalc", "cat": "geo", "cost": "Free", "url": "https://www.suncalc.org", "what": "Sun position and shadow direction for any place, date and time.", "tip": "Drag the time slider until the shadows match.", "checked": "2026-11"},
    {"id": "sentinel", "name": "Copernicus Browser", "cat": "geo", "cost": "Free", "url": "https://browser.dataspace.copernicus.eu", "what": "Free Sentinel satellite imagery, updated every few days (it replaced Sentinel Hub's EO Browser, shut down in March 2026).", "tip": "Compare two dates side by side to spot fires, floods and new construction.", "checked": "2026-11"},
    {"id": "flightradar", "name": "Flightradar24", "cat": "transport", "cost": "Freemium", "url": "https://www.flightradar24.com", "what": "Live and historical flight tracking by registration or flight number.", "tip": "Private jets often reveal their owners' movements.", "checked": "2026-11"},
    {"id": "marinetraffic", "name": "MarineTraffic", "cat": "transport", "cost": "Paid (3 free looks)", "status": "paywalled", "note": "Since 2025 most details sit behind a subscription after three free unlocks.", "url": "https://www.marinetraffic.com", "what": "Ship positions and port calls from AIS signals.", "tip": "Yachts have names and IMO/MMSI numbers to pivot on.", "checked": "2026-11"},
    {"id": "osintframework", "name": "OSINT Framework", "cat": "method", "cost": "Free", "url": "https://osintframework.com", "what": "A clickable map of hundreds of OSINT resources by category.", "tip": "Start here when you don't know which source holds a record.", "checked": "2026-11"},
    {"id": "bellingcat", "name": "Bellingcat Online Investigations Toolkit", "cat": "method", "cost": "Free", "url": "https://bellingcat.gitbook.io/toolkit", "what": "A curated, maintained guide to investigation tools.", "tip": "Read the guides, not just the links.", "checked": "2026-11"},
    {"id": "tracelabs", "name": "Trace Labs", "cat": "method", "cost": "Free", "url": "https://www.tracelabs.org", "what": "Ethical search-party events finding leads on real missing-persons cases.", "tip": "The best real-world practice there is, for a good cause.", "checked": "2026-11"},
    {"id": "maltego", "name": "Maltego", "cat": "method", "cost": "Freemium", "url": "https://www.maltego.com", "what": "Graph tool to link people, domains, companies and more.", "tip": "The Community edition is enough to learn.", "checked": "2026-11"},
    {"id": "spiderfoot", "name": "SpiderFoot", "cat": "method", "cost": "Free", "status": "unmaintained", "note": "The open-source version is effectively abandoned since Intel 471 bought it; modules break as sites change.", "url": "https://github.com/smicallef/spiderfoot", "what": "Open-source automation that runs many lookups on one selector.", "tip": "Automation finds leads; you still verify them.", "checked": "2026-11"},
]

# Gadgets: interactive helpers on the kit page (#kit/<id>), each a Form in client_code/Gadgets.
GADGETS = [
    {"id": "dorkbuilder", "name": "Dork Builder", "icon": "search", "what": "Build precise search-engine queries with operators."},
    {"id": "permutator", "name": "Username Permutator", "icon": "users", "what": "Turn a name into the usernames people actually pick."},
    {"id": "emailperm", "name": "Email Permutator", "icon": "mail", "what": "List the likely work-email formats for a person and a domain."},
    {"id": "exifreader", "name": "EXIF Reader", "icon": "camera", "what": "Read a photo's hidden metadata, privately in your browser."},
    {"id": "snowflake", "name": "ID & Time Decoder", "icon": "clock", "what": "Turn social-media post IDs and Unix timestamps into dates."},
    {"id": "grader", "name": "Source Grader", "icon": "target", "what": "Grade a source and a piece of information with the Admiralty code."},
]

# The Admiralty (NATO) grading system: source reliability A-F, information credibility 1-6.
REL = {
    "A": "Completely reliable",
    "B": "Usually reliable",
    "C": "Fairly reliable",
    "D": "Not usually reliable",
    "E": "Unreliable",
    "F": "Reliability cannot be judged",
}
CRED = {
    "1": "Confirmed by other sources",
    "2": "Probably true",
    "3": "Possibly true",
    "4": "Doubtful",
    "5": "Improbable",
    "6": "Truth cannot be judged",
}


def tool_by_id(tool_id):
    for t in TOOLS + GADGETS:
        if t["id"] == tool_id:
            return t
    return None
