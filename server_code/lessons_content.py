"""The Academy's curriculum: 8 modules x 3 lessons, each with a briefing, field steps, tools and a quiz.

Content only (no Anvil calls). Academy.py serves it and grades the quizzes, so the answers never reach
the browser before someone has answered. Text may use **bold** and `code`; the page renders those two.
`tools` are ids from the Field Kit library (OS.TOOLS in web/pages/_osinty.html); test_server.py checks
that every id exists there.
"""

MODULES: list = [
    {
        "id": "m1", "num": 1, "title": "The Investigator's Mindset", "tag": "Foundations", "icon": "eye",
        "blurb": "What open-source intelligence really is, the law you work inside, and how to stay invisible while you look.",
        "lessons": [
            {
                "id": "m1l1", "title": "What OSINT is (and isn't)", "minutes": 6,
                "summary": "Open sources, the intelligence cycle, and the difference between information and intelligence.",
                "body": [
                    "**Open-source intelligence (OSINT)** is intelligence produced from information anyone can lawfully get: websites, social media, news, public records, company filings, maps, photos, archives. Nothing is hacked, bought on the black market or obtained by lying.",
                    "Information is not intelligence. A username is information. Knowing that the username belongs to your subject, that it was active last week in Lisbon, and what that means for your client's question: that is intelligence. Your value as an investigator is the **analysis**, not the search.",
                    "Professionals work in a loop called the **intelligence cycle**: *plan* (what exactly is the question?), *collect* (gather sources), *process* (organise, translate, preserve), *analyse* (what does it mean, how sure are we?), and *disseminate* (report). Then the answer raises new questions and you go round again.",
                    "Most beginners skip planning and drown in tabs. A good investigator writes the question down first: *Where does Martin Kessler work now?* is a question you can answer. *Find everything about Martin* is not."
                ],
                "steps": [
                    "Write the client's question as one sentence you could answer with a fact.",
                    "List what you already know (names, usernames, photos, places, dates). These are your **selectors**.",
                    "For each selector, list which sources might mention it.",
                    "Collect, then stop and ask: does this answer the question? If not, what's the next pivot?"
                ],
                "tools": ["osintframework", "bellingcat"],
                "field_note": "Keep a running log from minute one: time, what you searched, where, what you found. Your future self (and the court) will thank you.",
                "quiz": [
                    {"q": "Which of these is NOT open-source intelligence?",
                     "options": ["A company's public annual report", "A post on a public social media profile",
                                 "Logging into someone's email with a guessed password", "An archived copy of a website"],
                     "answer": 2, "why": "Accessing an account without permission is unauthorised access (hacking), a crime almost everywhere. OSINT only uses lawfully available sources."},
                    {"q": "What turns information into intelligence?",
                     "options": ["Collecting more of it", "Analysis that answers a specific question", "Putting it in a spreadsheet", "Getting it from a paid database"],
                     "answer": 1, "why": "Intelligence is analysed information that answers the client's question, with a judgement of how reliable it is."},
                    {"q": "What is the first step of the intelligence cycle?",
                     "options": ["Collection", "Planning and direction", "Analysis", "Reporting"],
                     "answer": 1, "why": "Planning: defining the question and what you need. Skipping it is the most common rookie mistake."}
                ]
            },
            {
                "id": "m1l2", "title": "The law, ethics and the line you don't cross", "minutes": 8,
                "summary": "Pretexting, privacy law, licensing and why 'legal' and 'ethical' aren't the same thing.",
                "body": [
                    "Investigators work **inside** the law, never around it. The rules depend on where you and your subject are, so always check locally, but some lines are nearly universal: no unauthorised access to accounts or devices, no impersonating police or officials, no stalking or harassment, no buying stolen data.",
                    "**Pretexting** (lying about who you are to get information) is heavily restricted. In the US, the Gramm-Leach-Bliley Act forbids it for financial information and a 2006 federal law forbids it for phone records. Many places treat it as fraud. OSINT doesn't need it: you read what's already public.",
                    "Privacy and data-protection laws (the GDPR in Europe, PIPEDA and Québec's Law 25 in Canada, and many others) govern how you **store and use** personal information, even when you found it publicly. In the US, the Fair Credit Reporting Act controls background checks used for jobs, housing or credit, and the Driver's Privacy Protection Act limits motor-vehicle records.",
                    "Legal is the floor, not the ceiling. Before you dig, ask: is there a legitimate purpose? Is the depth proportionate? Could this information get someone hurt if the client misuses it? Good investigators turn down clients who want to find an ex-partner who has moved away."
                ],
                "steps": [
                    "Write down the legitimate purpose of each job before you start (fraud claim, court service, due diligence...).",
                    "Check which jurisdiction's laws apply: yours, the client's and the subject's.",
                    "Collect only what the question needs (data minimisation).",
                    "Refuse or escalate when a request smells like stalking, revenge or harassment."
                ],
                "tools": ["osintframework"],
                "field_note": "If you'd be uncomfortable explaining exactly how you got a piece of information to a judge, don't get it that way.",
                "quiz": [
                    {"q": "A client asks you to find the new address of an ex-partner who 'won't answer calls'. What do you do?",
                     "options": ["Find it: it's all public anyway", "Decline or dig into the purpose: this is a classic stalking red flag",
                                 "Find it but only give the city", "Call the ex pretending to be a delivery company"],
                     "answer": 1, "why": "Locating someone who has chosen to cut contact can put them in danger. Ethical investigators verify purpose and decline these jobs."},
                    {"q": "What is pretexting?",
                     "options": ["Reading the text before a search result", "Obtaining information by pretending to be someone else",
                                 "Writing a report's introduction", "Searching in another language"],
                     "answer": 1, "why": "Pretexting means using a false identity or story to get information. It is illegal for many types of records."},
                    {"q": "Information you found on a public website...",
                     "options": ["Is free of any legal duties once you have it", "May still be personal data that privacy laws protect",
                                 "Can be sold to anyone", "Must be deleted within 24 hours"],
                     "answer": 1, "why": "Being public doesn't remove protection: laws like the GDPR still govern how you store, use and share personal data."}
                ]
            },
            {
                "id": "m1l3", "title": "OPSEC: look without being seen", "minutes": 7,
                "summary": "Protect yourself, your client and your case from tipping off the subject.",
                "body": [
                    "**Operational security (OPSEC)** means not revealing that an investigation exists. A careless click can warn your subject: some networks tell people who viewed their profile, a stray 'like' is public, and a visit from your office IP can show up in a small website's logs.",
                    "Work from a **separate browser profile** (or a dedicated machine or virtual machine) that is never logged into your personal accounts. A VPN hides your home or office address from the sites you visit. Turn off auto-play and never download unknown files to your main computer.",
                    "Some investigators use research accounts (sometimes called *sock puppets*) to view content that needs a login. Know the risks: many platforms forbid fake accounts in their terms, some jurisdictions and employers restrict them, and you must **never interact** with the subject through one. Viewing is research; befriending or messaging under a false identity crosses into deception.",
                    "Prefer passive sources: search-engine caches, archives and third-party mirrors let you read without touching the subject's own page at all."
                ],
                "steps": [
                    "Create an investigation-only browser profile with no personal logins.",
                    "Check each platform's 'who viewed my profile' features before you browse.",
                    "Never like, follow, comment, connect or message during research.",
                    "Read through archives first (Wayback, archive.today) before visiting the live page."
                ],
                "tools": ["wayback", "archivetoday"],
                "field_note": "Assume every click leaves a footprint. Ask yourself who could see it.",
                "quiz": [
                    {"q": "Which action is most likely to tip off your subject?",
                     "options": ["Reading an archived copy of their blog", "Viewing their professional-network profile while logged into your own account",
                                 "A web search for their name", "Checking a business registry"],
                     "answer": 1, "why": "Professional networks often show people who viewed their profile. Use a logged-out or separate research profile."},
                    {"q": "During research with a research account, you should...",
                     "options": ["Send a friend request to see more", "Only observe, never interact with the subject",
                                 "Comment to start a conversation", "Like old posts so you blend in"],
                     "answer": 1, "why": "Interacting turns research into deception and can tip off the subject or taint your evidence."},
                    {"q": "Why read a page through an archive first?",
                     "options": ["Archives are always newer", "You don't touch the subject's own server, and you may see deleted content",
                                 "It's the only way to see images", "Archives remove ads"],
                     "answer": 1, "why": "Archives are passive and often keep versions the subject has since edited or deleted."}
                ]
            }
        ]
    },
    {
        "id": "m2", "num": 2, "title": "Search Like a Detective", "tag": "Search", "icon": "search",
        "blurb": "Search operators, other engines, and the archives that remember what the web forgot.",
        "lessons": [
            {
                "id": "m2l1", "title": "Search operators (dorking)", "minutes": 8,
                "summary": "Make a search engine do exactly what you want with quotes, site:, filetype: and friends.",
                "body": [
                    "Search engines hide enormous power behind small commands called **operators**. Combining them is nicknamed *dorking*. They turn a vague search into a precise one.",
                    "The essentials: `\"exact phrase\"` matches words in that order. `site:example.org` searches one website (or `site:.gov` a whole domain type). `filetype:pdf` finds documents. `intitle:` and `inurl:` look only in the page title or address. A minus sign excludes: `-jobs`. `OR` (in capitals) gives alternatives. `before:2024-01-01` and `after:` limit dates on Google.",
                    "Stack them: `\"Martin Kessler\" site:linkedin.com Saskatoon` or `\"annual report\" \"VK Media\" filetype:pdf`. Documents are gold: PDFs and spreadsheets often contain names, phone numbers and internal details that never appear on the website itself.",
                    "Operators change over time (Google retired `cache:` in 2024), and every engine supports a slightly different set, so test them before trusting a zero-result search."
                ],
                "steps": [
                    "Start with the exact name in quotes.",
                    "Add a `site:` for the platforms that matter (a registry, a forum, a social network).",
                    "Add `filetype:pdf` or `filetype:xlsx` to hunt documents.",
                    "Exclude noise with `-` (namesakes, job sites), then try the same dork on another engine."
                ],
                "tools": ["googleadvanced", "bing", "dorkbuilder"],
                "field_note": "Build your dorks in the Field Kit's Dork Builder and save the ones that work: they're reusable.",
                "quiz": [
                    {"q": "Which search finds PDF documents mentioning the exact phrase 'VK Media' only on .gov sites?",
                     "options": ["VK Media pdf gov", "\"VK Media\" filetype:pdf site:.gov", "site:VK Media filetype:.gov", "intitle:pdf VK -gov"],
                     "answer": 1, "why": "Quotes for the exact phrase, filetype: for PDFs and site: for the .gov domain."},
                    {"q": "What does a minus sign before a word do?",
                     "options": ["Makes it optional", "Excludes results containing it", "Searches for its opposite", "Lowers its ranking slightly"],
                     "answer": 1, "why": "`-word` removes results containing that word. Great for filtering out namesakes."},
                    {"q": "Why are documents (PDF, XLSX) so valuable?",
                     "options": ["They're always more recent", "They often hold names, numbers and details that never appear on web pages",
                                 "Search engines rank them first", "They can't be faked"],
                     "answer": 1, "why": "Minutes, reports, lists and forms often leak exactly the details you need, plus metadata like author names."}
                ]
            },
            {
                "id": "m2l2", "title": "Beyond Google", "minutes": 6,
                "summary": "Different engines index different worlds. Use them all.",
                "body": [
                    "No search engine indexes the whole web. Google, **Bing**, **Yandex**, DuckDuckGo, Baidu and others each crawl differently, rank differently and remove different things. A result missing on one is often sitting on page one of another.",
                    "Yandex is famous among investigators for reverse image search of faces and places, and for Eastern European content. Bing has operators Google lacks, such as `ip:` to find sites hosted on one server. Regional engines are essential when your subject lives in another country.",
                    "Search **in the subject's language**. A Brazilian company is described in Portuguese; a Latvian court notice is in Latvian. Translate your keywords, including local spellings of names (Krūmiņa, Krumina, Kruminya), and let the browser translate the results.",
                    "Specialised engines exist for nearly everything: code, academic papers, court rulings, patents, ships, flights, leaks. The OSINT Framework is a map of them."
                ],
                "steps": [
                    "Run your best query on at least three engines.",
                    "Translate keywords into the subject's language and local spellings.",
                    "Use a regional engine for the subject's country.",
                    "Look up a specialised engine for the kind of record you need."
                ],
                "tools": ["bing", "yandex", "osintframework"],
                "field_note": "Note which engine found what. If a result vanishes later, you'll know where to look again.",
                "quiz": [
                    {"q": "Why use several search engines?",
                     "options": ["They all return the same results faster", "Each indexes and ranks differently, so results differ",
                                 "Google blocks investigators", "It's required by law"],
                     "answer": 1, "why": "Different crawlers, indexes and removal policies mean each engine finds things the others miss."},
                    {"q": "Your subject is a small business in Brazil. Best approach?",
                     "options": ["Search only in English", "Translate your keywords to Portuguese and search local sources",
                                 "Assume it has no online presence", "Use only image search"],
                     "answer": 1, "why": "Local businesses are described in the local language on local sites and registries."},
                    {"q": "Which engine is widely used by investigators for reverse image search of faces and places?",
                     "options": ["Yandex", "A dictionary site", "A weather site", "None exist"],
                     "answer": 0, "why": "Yandex Images is known for strong face and landmark matching."}
                ]
            },
            {
                "id": "m2l3", "title": "Archives and preserving evidence", "minutes": 7,
                "summary": "The Wayback Machine, archive.today, and how to capture a page so it stands up later.",
                "body": [
                    "The web forgets; archives don't. The **Wayback Machine** (web.archive.org) has stored hundreds of billions of page captures since 1996. **archive.today** captures pages on demand, including some that block other archivers.",
                    "Use archives to see what a page said **before** it was edited or deleted: an old 'About us' page with a founder's name, a staff list, a deleted post, a price list. Wayback can also list every URL it knows for a domain (its CDX index), revealing forgotten pages.",
                    "**Preserve** what you find the moment you find it. Content disappears, sometimes because your subject noticed the attention. Capture the page to an archive, take a full-page screenshot showing the URL and the date and time, and save the file.",
                    "For evidence that may go to court, record *how* you captured it, when, and from which system. Tools like Hunchly do this automatically. Some investigators compute a **hash** of saved files so they can prove later the file hasn't changed."
                ],
                "steps": [
                    "Look up the subject's website in the Wayback Machine calendar.",
                    "Compare the oldest and newest captures: what changed?",
                    "Capture key pages yourself (Save Page Now or archive.today).",
                    "Screenshot with URL and timestamp visible, and log it."
                ],
                "tools": ["wayback", "archivetoday", "hunchly"],
                "field_note": "Capture first, analyse later. A page you didn't save is a page you can't prove.",
                "quiz": [
                    {"q": "A company changed its 'About us' page last month. How do you see the old version?",
                     "options": ["Ask the company", "Look it up in the Wayback Machine", "Clear your cache", "It's impossible"],
                     "answer": 1, "why": "Archives keep earlier captures of pages, often with details since removed."},
                    {"q": "What should a good evidence screenshot show?",
                     "options": ["Only the interesting sentence", "The full page with the URL and the date/time visible",
                                 "Your own desktop wallpaper", "A cropped photo"],
                     "answer": 1, "why": "Context (URL, date, time) shows where and when the content existed."},
                    {"q": "Why compute a hash of a saved file?",
                     "options": ["To make it smaller", "To prove later that the file hasn't been altered", "To encrypt it", "To find its author"],
                     "answer": 1, "why": "A hash is a fingerprint; if the file changes, the hash changes."}
                ]
            }
        ]
    },
    {
        "id": "m3", "num": 3, "title": "People, Usernames & Records", "tag": "People", "icon": "user",
        "blurb": "Pivot from one handle to a whole online life, and find the paper trail people leave in public records.",
        "lessons": [
            {
                "id": "m3l1", "title": "Username pivoting", "minutes": 7,
                "summary": "People reuse handles. One username can unlock a dozen accounts.",
                "body": [
                    "People are creatures of habit: the handle they chose at fifteen often follows them to every new platform. A **pivot** is using one selector (a username) to find new selectors (other accounts, a real name, a photo, a city).",
                    "Username checkers such as **WhatsMyName** and the open-source tool **Sherlock** test a handle on hundreds of sites at once. Then search the handle in quotes on search engines: forum posts, old gaming profiles and comment sections rarely show up in checkers.",
                    "Try **variants**: `mkess84`, `m.kess84`, `mkessler84`, `mkess_84`. Birth years, favourite numbers and initials repeat. The Field Kit's Username Permutator generates variants for you.",
                    "Beware false positives. A common handle like `jsmith` exists on every site and belongs to many people. Confirm a match with something shared between accounts: the same profile photo, bio wording, location, friends or writing style."
                ],
                "steps": [
                    "Run the handle through a username checker.",
                    "Search the handle in quotes on several engines.",
                    "Generate and test variants (years, separators, initials).",
                    "Confirm each hit with at least one shared detail before you trust it."
                ],
                "tools": ["whatsmyname", "sherlock", "permutator"],
                "field_note": "A rare username is a strong selector. A common one is a trap.",
                "quiz": [
                    {"q": "You found the username 'mkess84' on a forum. What's the best next step?",
                     "options": ["Assume every 'mkess84' online is the same person", "Check it across many sites, then confirm matches with shared details",
                                 "Message the user to ask", "Ignore it, usernames are useless"],
                     "answer": 1, "why": "Pivot broadly, then verify each match with something shared (photo, location, bio)."},
                    {"q": "Which username is the WEAKEST selector?",
                     "options": ["kittenwhisperer_1987", "mkess84", "john", "leahsketches"],
                     "answer": 2, "why": "A very common handle is used by thousands of unrelated people."},
                    {"q": "What confirms two accounts belong to the same person?",
                     "options": ["They're on different websites", "They share the same profile photo, bio details or location",
                                 "They were both created this year", "Both have many followers"],
                     "answer": 1, "why": "Shared, specific details link accounts; matching handles alone don't."}
                ]
            },
            {
                "id": "m3l2", "title": "Emails and phone numbers", "minutes": 7,
                "summary": "Guess, verify and pivot from contact details, without crossing ethical lines.",
                "body": [
                    "Companies use predictable email formats: `first.last@`, `flast@`, `firstl@`. Find one real address from the company (a press release, a PDF) and you can predict the rest. The Field Kit's Email Permutator lists the common patterns.",
                    "Search the email in quotes: it may appear in forum signatures, documents, domain registrations, or scam-report sites. Services like **Have I Been Pwned** tell you which known data breaches an address appears in, which shows which sites the person used. Never download or use leaked passwords or breach dumps: that is handling stolen data.",
                    "Don't trigger password-reset emails to 'confirm' an account exists: the owner gets a notification (tipping them off) and it can breach the site's terms.",
                    "Phone numbers: normalise the format (country code, no spaces) and search the variants. Numbers show up on classified ads, business listings and messaging apps. A number's country and original carrier hint at where its owner was when they got it."
                ],
                "steps": [
                    "Find one confirmed address at the domain and work out the pattern.",
                    "Search the email and its username part in quotes.",
                    "Check breach-notification services for which sites it was used on.",
                    "Normalise phone numbers and search several formats."
                ],
                "tools": ["hibp", "emailperm", "googleadvanced"],
                "field_note": "The part before the @ is often a username too. Pivot on it.",
                "quiz": [
                    {"q": "A company's press contact is anna.berg@company.example. What's the likely address of Tom Wills?",
                     "options": ["tw@company.example", "tom.wills@company.example", "wills.t@company.example", "Impossible to guess"],
                     "answer": 1, "why": "Companies usually use one pattern. first.last matches the known address."},
                    {"q": "Is it OK to trigger a password reset to see if an account exists?",
                     "options": ["Yes, it's the quickest method", "No: it notifies the owner and can breach the site's terms",
                                 "Only on weekends", "Only for email accounts"],
                     "answer": 1, "why": "It tips off the subject and interferes with their account. Use passive methods."},
                    {"q": "What can breach-notification services ethically tell you?",
                     "options": ["The person's password", "Which known breaches (and so which sites) an email appears in",
                                 "Their home address", "Their bank balance"],
                     "answer": 1, "why": "Services like Have I Been Pwned only show breach names, not the leaked data itself."}
                ]
            },
            {
                "id": "m3l3", "title": "Public records", "minutes": 8,
                "summary": "Courts, property, businesses, licences and notices: the paper trail of a life.",
                "body": [
                    "Many life events create **public records**: court cases and judgments, property sales, company directorships, professional licences, marriage or death notices, bankruptcies, liens. What is public varies enormously by country and region.",
                    "Court databases (PACER and CourtListener in the US, CanLII in Canada, national court portals elsewhere) show lawsuits, judgments and sometimes addresses and dates of birth. Property records show who owns what and when it changed hands. Obituaries and wedding announcements list relatives and hometowns.",
                    "Commercial **people-search sites** aggregate these records, but they are often wrong, mixing namesakes and outdated addresses. Treat them as leads to verify against the original record, never as proof. In many places, using them for employment or tenant screening is regulated.",
                    "Records give you **anchors**: a middle initial, a birth year, a former address. Anchors let you separate your Martin Kessler from the forty others."
                ],
                "steps": [
                    "Identify which records are public in the subject's jurisdiction.",
                    "Search courts and property records by name and known address.",
                    "Extract anchors: middle names, birth year, past addresses, relatives.",
                    "Verify anything from people-search sites against the original record."
                ],
                "tools": ["courtlistener", "canlii", "opencorporates"],
                "field_note": "Namesakes are the number one cause of wrong reports. Anchor every identification to at least two independent details.",
                "quiz": [
                    {"q": "A people-search site lists an address for your subject. You should...",
                     "options": ["Put it straight in your report", "Treat it as a lead and verify it against original records",
                                 "Visit the address immediately", "Ignore all such sites forever"],
                     "answer": 1, "why": "Aggregators mix namesakes and old data. Verify with primary sources."},
                    {"q": "What is an 'anchor' in identification?",
                     "options": ["A ship record", "A specific detail (like birth year or middle initial) that separates your subject from namesakes",
                                 "A link to another website", "The first search result"],
                     "answer": 1, "why": "Anchors are distinguishing details you use to confirm identity."},
                    {"q": "Which is typically a public record?",
                     "options": ["Medical files", "A court judgment", "Bank statements", "Private emails"],
                     "answer": 1, "why": "Court judgments are generally public; medical, bank and email records are private."}
                ]
            }
        ]
    },
    {
        "id": "m4", "num": 4, "title": "Social Media Intelligence", "tag": "SOCMINT", "icon": "users",
        "blurb": "Read profiles like a detective: networks, routines, timelines and the tells of a fake.",
        "lessons": [
            {
                "id": "m4l1", "title": "Mapping a profile", "minutes": 7,
                "summary": "Bios, friends, tags and check-ins: what a profile says about its owner's world.",
                "body": [
                    "A profile is more than its posts. The **bio** gives roles, cities and other handles. The **profile and cover photos** can be reverse-searched. The account's **creation date** and first posts reveal whether it's long-lived or freshly made.",
                    "The **network** often says more than the person: friends, followers, people who comment regularly, tagged photos posted by *others*. Someone who keeps their own account private is often visible in friends' public photos, school or club pages, and family posts.",
                    "Check-ins, tagged places, sports-tracking apps and event pages show where someone goes. Reviews (restaurants, shops, apps) are a forgotten goldmine: people review the gym near home and the dentist near work.",
                    "Write what you see as **observations**, not conclusions: 'posts tagged at Riverside Climbing Gym 14 times since March' rather than 'lives in Riverside'."
                ],
                "steps": [
                    "Record handle, display name, bio, creation date and profile photo.",
                    "List the accounts that interact most: friends, family, colleagues.",
                    "Collect places from check-ins, tags and reviews.",
                    "Look for the subject in other people's public content."
                ],
                "tools": ["whatsmyname", "googlelens"],
                "field_note": "When the front door is locked (private account), walk around to the friends' windows (their public posts).",
                "quiz": [
                    {"q": "Your subject's account is private. Where might you still see them?",
                     "options": ["Nowhere", "In public posts and tagged photos by friends, clubs and family", "Only in paid databases", "In their private messages"],
                     "answer": 1, "why": "Other people's public content frequently includes private-account users."},
                    {"q": "What does a very recent account creation date suggest?",
                     "options": ["Nothing at all", "It could be new, replaced, or fake: worth noting", "It's definitely real", "The owner is famous"],
                     "answer": 1, "why": "Fresh accounts are common for scams and replacements. It's a data point to weigh."},
                    {"q": "Which is the better note?",
                     "options": ["'Lives in Riverside'", "'Tagged at Riverside Climbing Gym 14 times since March'", "'Is probably rich'", "'Seems nice'"],
                     "answer": 1, "why": "Record observations with evidence; conclusions come later in analysis."}
                ]
            },
            {
                "id": "m4l2", "title": "Timelines and patterns of life", "minutes": 7,
                "summary": "When people post reveals where they are and how they live.",
                "body": [
                    "Lay posts on a **timeline**. Gaps and bursts tell stories: a sudden silence, a burst of posts from a new city, a shift in posting hours.",
                    "Posting times reveal **time zones**. If someone 'in Halifax' posts every day between 03:00 and 05:00 Halifax time, they may be five hours ahead, perhaps in Europe. Combine this with language, slang, prices and weather in their posts.",
                    "A **pattern of life** is someone's routine: gym on Tuesdays, coffee shop on Saturday mornings. Investigators use it for legitimate purposes like serving court papers or confirming an insurance claim. Be careful: the same information is exactly what a stalker wants, which is why it belongs in a secure case file, never in public.",
                    "Deleted posts and edits matter. Archives, quote-posts, replies and screenshots by others often keep what the subject removed."
                ],
                "steps": [
                    "Export or list posts with dates and times.",
                    "Convert times to UTC, then test candidate time zones.",
                    "Mark gaps, bursts and location changes.",
                    "Search archives and replies for deleted content."
                ],
                "tools": ["snowflake", "wayback"],
                "field_note": "Many platform post IDs encode the exact creation time. The Field Kit's ID decoder reads them.",
                "quiz": [
                    {"q": "Someone claiming to live in Halifax always posts between 03:00 and 05:00 Halifax time. What might that suggest?",
                     "options": ["They're a night owl, nothing more to see", "They may actually be in another time zone, e.g. Europe",
                                 "Their phone clock is broken", "They're a bot"],
                     "answer": 1, "why": "Consistent odd hours suggest a different time zone. Test it against other clues; don't conclude on one."},
                    {"q": "Where can deleted posts sometimes still be found?",
                     "options": ["Nowhere", "Archives, quotes, replies and screenshots by others", "In the platform's terms of service", "On the subject's phone only"],
                     "answer": 1, "why": "Copies often survive elsewhere even when the original is gone."},
                    {"q": "Pattern-of-life information should be...",
                     "options": ["Posted publicly to warn people", "Kept in the secure case file and shared only as the purpose requires",
                                 "Sold to data brokers", "Sent to the subject"],
                     "answer": 1, "why": "It's sensitive and dangerous in the wrong hands. Share only what the legitimate purpose needs."}
                ]
            },
            {
                "id": "m4l3", "title": "Spotting fakes and catfish", "minutes": 8,
                "summary": "Stock photos, AI faces and the classic romance-scam script.",
                "body": [
                    "Fake profiles power romance scams, fraud and influence campaigns. The quickest test is a **reverse image search** of the profile photo: stolen photos often belong to a model, an influencer or a stock-photo library.",
                    "AI-generated faces have tells: the eyes sit in exactly the same place in every image, earrings or glasses don't match left to right, hair melts into the background, teeth and ears are oddly shaped, and backgrounds contain warped, unreadable objects.",
                    "Account signals: a recent creation date, few photos (all professional), followers that are themselves empty accounts, inconsistent details (a 'US Navy captain' who writes like he's never been to the US).",
                    "Romance scams follow a script: fast love, an exotic job that explains why they can't video-call (oil rig, military deployment, ship), then a crisis that needs money (customs fees, 'leave papers', medical bills). Payment by gift cards, crypto or wire is the final red flag."
                ],
                "steps": [
                    "Reverse-search every profile photo on several engines.",
                    "Check the photo for AI artefacts (eyes, ears, accessories, background).",
                    "Look at the account's age, followers and posting history.",
                    "Compare the story with the classic scam script."
                ],
                "tools": ["googlelens", "tineye", "yandex"],
                "field_note": "One reverse image search has saved more victims' savings than any lecture.",
                "quiz": [
                    {"q": "Which is a common tell of an AI-generated face?",
                     "options": ["A sharp, readable background", "Mismatched earrings and a warped background", "A visible watermark from a camera brand", "Black and white colouring"],
                     "answer": 1, "why": "Generators struggle with symmetry of accessories and coherent backgrounds."},
                    {"q": "A match you've never met says he's a soldier abroad and needs money for 'leave papers'. This is...",
                     "options": ["A normal military procedure", "A classic romance-scam script", "A sign of honesty", "Something to pay quickly"],
                     "answer": 1, "why": "Soldiers don't pay for leave; 'leave papers' is a well-known scam line."},
                    {"q": "What's the fastest first test of a suspicious profile photo?",
                     "options": ["Ask them for another photo", "Reverse image search", "Count their followers", "Check the weather"],
                     "answer": 1, "why": "Reverse search often finds the real owner of a stolen photo in seconds."}
                ]
            }
        ]
    },
    {
        "id": "m5", "num": 5, "title": "Images & Video", "tag": "Imagery", "icon": "camera",
        "blurb": "Find a photo's origin, read the data hidden inside it, and verify video before you believe it.",
        "lessons": [
            {
                "id": "m5l1", "title": "Reverse image search", "minutes": 7,
                "summary": "Find where else a picture lives, and its earliest copy.",
                "body": [
                    "A **reverse image search** finds copies and look-alikes of a picture. Use several engines: **Google Lens** is strong on products and places, **Yandex** on faces and landmarks, **Bing Visual Search** on general content, and **TinEye** lets you sort matches by date to find the **oldest** copy (usually the closest to the original).",
                    "Crop before you search. A full photo of a man in a street matches millions of streets; a crop of just the shop sign or just the face gives sharper results. Flip the image horizontally too: scammers mirror stolen photos to beat simple matching.",
                    "Results tell a story: a photo that appears on stock-photo sites, or on an account with a different name, is not what it claims to be. An image first posted years before the 'event' it supposedly shows is recycled.",
                    "No results proves nothing: the image may be original, private, or simply not indexed yet."
                ],
                "steps": [
                    "Search the whole image on at least three engines.",
                    "Crop distinctive parts (faces, signs, logos) and search each.",
                    "Sort by date to find the earliest copy.",
                    "Try a mirrored version if nothing matches."
                ],
                "tools": ["googlelens", "tineye", "yandex", "bingvisual"],
                "field_note": "The oldest copy wins. The first place an image appeared is usually its source.",
                "quiz": [
                    {"q": "Why crop an image before a reverse search?",
                     "options": ["Smaller files upload faster", "A distinctive detail gives sharper matches than a generic full scene",
                                 "Engines only accept squares", "It removes metadata"],
                     "answer": 1, "why": "Focused crops of faces, signs or logos match far better."},
                    {"q": "Which tool lets you sort matches by date to find the oldest copy?",
                     "options": ["TinEye", "A calculator", "A map", "A dictionary"],
                     "answer": 0, "why": "TinEye can sort results by oldest, which helps find the source."},
                    {"q": "A reverse search finds nothing. This means...",
                     "options": ["The photo is definitely real", "Nothing certain: it may be original, private or unindexed", "The photo is AI", "The person doesn't exist"],
                     "answer": 1, "why": "Absence of evidence isn't evidence of absence."}
                ]
            },
            {
                "id": "m5l2", "title": "Metadata (EXIF) and documents", "minutes": 7,
                "summary": "The data hidden inside files: cameras, times, places and authors.",
                "body": [
                    "Digital photos usually carry **EXIF metadata**: camera make and model, the date and time taken, exposure settings, and on phones often **GPS coordinates**. Documents carry metadata too: author names, company names, software versions and edit dates in PDFs and Office files.",
                    "Most big social networks **strip** EXIF when you upload, so a photo downloaded from them rarely has GPS. But originals sent by email, posted on some forums and blogs, or shared as 'files' rather than 'photos' often keep everything.",
                    "Read metadata with **ExifTool** or the Field Kit's EXIF Reader (it runs in your browser, so the photo never leaves your device). Convert GPS to a map pin and look.",
                    "Metadata can be edited or wrong (a camera with the wrong clock). Treat it as one witness, and corroborate it: does the GPS match the scene? Does the time match the shadows?"
                ],
                "steps": [
                    "Get the most original copy of the file you can.",
                    "Read the metadata: camera, time, GPS, software, author.",
                    "Map any coordinates and compare with the scene.",
                    "Corroborate time and place with independent clues."
                ],
                "tools": ["exifreader", "exiftool"],
                "field_note": "Always ask the client for the original file, not a screenshot or a forwarded copy.",
                "quiz": [
                    {"q": "You download a photo from a big social network. Will it have GPS metadata?",
                     "options": ["Always", "Usually not: most big networks strip it on upload", "Only if it's in colour", "Only at night"],
                     "answer": 1, "why": "Major platforms remove EXIF for privacy. Seek the original file."},
                    {"q": "Which can document metadata reveal?",
                     "options": ["The author's name and company", "The reader's password", "The printer's ink level", "Nothing ever"],
                     "answer": 0, "why": "PDF and Office files often store author, organisation and edit history."},
                    {"q": "EXIF says a photo was taken at noon, but shadows are very long. You should...",
                     "options": ["Trust the EXIF", "Treat it as a conflict to resolve: the camera clock may be wrong or the file edited", "Trust the shadows only", "Ignore both"],
                     "answer": 1, "why": "Conflicting evidence must be explained. Metadata is one witness, not the judge."}
                ]
            },
            {
                "id": "m5l3", "title": "Verifying video", "minutes": 7,
                "summary": "Keyframes, first uploads, and the questions that expose recycled footage.",
                "body": [
                    "Video is images in a row, so the same tools apply. Grab **keyframes** (the InVID-WeVerify browser plugin does this automatically) and reverse-search them. Old footage recycled as 'breaking news' is the most common fake.",
                    "Find the **first upload**: search the platforms with keywords and dates, sort by oldest, and look for the account that posted it first. Contact the original uploader (as yourself, honestly) when you need permission or context.",
                    "Ask the five questions of verification: **who** filmed it, **when**, **where**, **why** (what's the uploader's agenda?) and **is it the original**? Check weather records for the claimed date, the length and direction of shadows, the language spoken and shop signs.",
                    "Deepfakes exist, but crude edits and miscaptions are far more common. Look for cuts, inconsistent audio and lighting, and text that contradicts the claim."
                ],
                "steps": [
                    "Extract keyframes and reverse-search them.",
                    "Find the earliest upload and its uploader.",
                    "Check weather, shadows, language and signs against the claim.",
                    "Write down who, when, where, why and whether it's the original."
                ],
                "tools": ["invid", "googlelens", "suncalc"],
                "field_note": "'Is this the original?' is the question that catches most fakes.",
                "quiz": [
                    {"q": "What is the most common kind of fake video?",
                     "options": ["Perfect deepfakes", "Real, older footage reshared with a false caption", "Hand-drawn animation", "Silent films"],
                     "answer": 1, "why": "Recycled and miscaptioned footage is far more common than deepfakes."},
                    {"q": "What does the InVID-WeVerify plugin help with?",
                     "options": ["Extracting keyframes to reverse-search", "Downloading music", "Booking flights", "Editing photos"],
                     "answer": 0, "why": "It extracts keyframes and links to reverse-search engines and other checks."},
                    {"q": "A video 'from yesterday' shows snow; weather records show 25°C and sun there yesterday. Conclusion?",
                     "options": ["It's authentic", "The claim is very likely false: wrong date or wrong place", "Weather records are always wrong", "It snowed indoors"],
                     "answer": 1, "why": "Environmental clues must match the claim."}
                ]
            }
        ]
    },
    {
        "id": "m6", "num": 6, "title": "Geolocation & Chronolocation", "tag": "GEOINT", "icon": "pin",
        "blurb": "Pin a photo to a spot on Earth and a moment in time using signs, shadows and satellites.",
        "lessons": [
            {
                "id": "m6l1", "title": "Reading the scene", "minutes": 8,
                "summary": "Signs, plates, roads and poles: the clues every street photo is full of.",
                "body": [
                    "**Geolocation** means finding where a photo or video was taken. Start broad (continent, country) and narrow down. Every scene is full of clues.",
                    "**Language and script** on signs narrow the country. **Licence plates** have national shapes and colours. **Driving side**, road markings (yellow or white centre lines), bollards, kerbs, traffic lights and street-name signs vary by country and even by city. **Utility poles**, power sockets, architecture, roof tiles and vegetation add more.",
                    "**Business names** are the jackpot: search the shop name plus the city. Phone numbers on signs carry area codes. A bus route number plus a colour scheme can identify a transit system.",
                    "Write each clue down with what it tells you and how sure you are. Geolocation is a chain of small inferences: one wrong link sends you to the wrong city."
                ],
                "steps": [
                    "List every readable text: signs, shop names, plates, phone numbers.",
                    "Note infrastructure: driving side, road lines, poles, bollards.",
                    "Note environment: vegetation, terrain, architecture, weather.",
                    "Narrow from country to city, then hunt the exact spot."
                ],
                "tools": ["streetview", "googleearth", "mapillary"],
                "field_note": "Text first. One readable shop sign beats ten vague hunches about trees.",
                "quiz": [
                    {"q": "Cars drive on the left and plates are yellow at the back. This narrows the country to...",
                     "options": ["Anywhere", "Countries that drive on the left, such as the UK", "Only the USA", "Only landlocked countries"],
                     "answer": 1, "why": "Left-hand traffic plus yellow rear plates is characteristic of the UK."},
                    {"q": "What is usually the strongest single clue in a street photo?",
                     "options": ["The colour of the sky", "A readable business name or phone number", "A pigeon", "The photo's file size"],
                     "answer": 1, "why": "Searchable text can lead directly to an address."},
                    {"q": "Why write down each clue with a confidence level?",
                     "options": ["To fill space", "Geolocation is a chain of inferences; you need to see which links are weak", "It's required by cameras", "To impress clients"],
                     "answer": 1, "why": "Tracking confidence shows where a wrong assumption might have crept in."}
                ]
            },
            {
                "id": "m6l2", "title": "Maps, satellites and street level", "minutes": 7,
                "summary": "Confirm a location by matching the photo to imagery from above and from the street.",
                "body": [
                    "Once you have a candidate area, **confirm** it. Google Earth and satellite maps show roof shapes, road layouts, car parks and field patterns from above. **Street View** and **Mapillary** let you stand where the photographer stood.",
                    "Match at least three fixed features: the shape of a building, a lamp post, a gap in a skyline, a mountain ridge. Moving things (cars, people, shop displays) don't count; they change.",
                    "When the area is large, query the map itself. **Overpass Turbo** searches OpenStreetMap data: 'every pharmacy within 100 m of a railway bridge in this city', for instance. Historical satellite imagery shows when something was built or demolished, which also dates a photo.",
                    "A confirmed geolocation is reproducible: someone else, following your notes and features, reaches the same spot."
                ],
                "steps": [
                    "Find the candidate area on satellite imagery.",
                    "Stand there in Street View or Mapillary and match the angle.",
                    "Confirm three or more fixed features.",
                    "Record coordinates and the features you matched."
                ],
                "tools": ["googleearth", "streetview", "mapillary", "overpass"],
                "field_note": "Moving objects lie. Buildings, poles and mountains don't.",
                "quiz": [
                    {"q": "Which features should you use to confirm a location?",
                     "options": ["Parked cars and pedestrians", "Fixed features like building shapes, poles and skylines", "Clouds", "Advertising posters only"],
                     "answer": 1, "why": "Fixed features persist; moving objects change between photo and imagery."},
                    {"q": "What does Overpass Turbo let you do?",
                     "options": ["Query OpenStreetMap for combinations of features", "Speed up your internet", "Translate signs", "Read EXIF"],
                     "answer": 0, "why": "It searches OSM data, e.g. all bridges near a river with a church nearby."},
                    {"q": "A confirmed geolocation should be...",
                     "options": ["A gut feeling", "Reproducible by someone following your notes", "Secret", "Based on one clue"],
                     "answer": 1, "why": "Reproducibility is what makes it evidence."}
                ]
            },
            {
                "id": "m6l3", "title": "Chronolocation: when was it taken?", "minutes": 7,
                "summary": "Shadows, sun position, weather and events put a clock on a photo.",
                "body": [
                    "**Chronolocation** answers *when*. The sun is a clock: once you know the place, the **direction and length of shadows** give the time of day and roughly the season. **SunCalc** shows the sun's position and shadow direction for any place and moment.",
                    "Weather is a calendar: historical weather records (snow, rain, clear sky) can rule dates in or out. Events, posters, shop window displays, construction progress on satellite images and the model years of cars all bracket the date.",
                    "Metadata, upload times and post IDs give upper limits: a photo can't have been taken after it was first posted.",
                    "Combine methods. Shadows say 'about 17:00', weather says 'one of three dry days that week', the first upload says 'before Tuesday': together they make a strong claim."
                ],
                "steps": [
                    "Measure shadow direction against a known north (from the map).",
                    "Test times and dates in SunCalc until the shadows match.",
                    "Check historical weather for the candidate dates.",
                    "Bracket the date with first-upload times and visible events."
                ],
                "tools": ["suncalc", "googleearth", "snowflake"],
                "field_note": "A photo can never be newer than its first upload. That's your hard upper limit.",
                "quiz": [
                    {"q": "Which tool shows sun position and shadow direction for a place and time?",
                     "options": ["SunCalc", "WHOIS", "TinEye", "Sherlock"],
                     "answer": 0, "why": "SunCalc models the sun's position and shadows anywhere, any time."},
                    {"q": "What gives a hard upper limit on when a photo was taken?",
                     "options": ["Its first known upload time", "Its file name", "The camera brand", "Its colours"],
                     "answer": 0, "why": "It can't have been taken after it was first posted."},
                    {"q": "Shadows in a northern-hemisphere photo point roughly north-east and are long. The time is likely...",
                     "options": ["Around midday", "Early evening (sun low in the south-west/west)", "Midnight", "Impossible to say anything"],
                     "answer": 1, "why": "Shadows point away from the sun. Long shadows to the north-east mean a low sun in the south-west: late afternoon or evening."}
                ]
            }
        ]
    },
    {
        "id": "m7", "num": 7, "title": "Companies, Domains & Money", "tag": "Corporate", "icon": "briefcase",
        "blurb": "Unmask who's behind a company or a website, and follow assets through public filings.",
        "lessons": [
            {
                "id": "m7l1", "title": "Business records and shell companies", "minutes": 8,
                "summary": "Registries, directors, registered agents and the tricks used to hide owners.",
                "body": [
                    "Companies must register, and registries are often public: **Companies House** (UK), **SEC EDGAR** (US public companies), state and provincial registries, and aggregators like **OpenCorporates** that search across over 100 jurisdictions.",
                    "A filing shows directors, officers, registered addresses, incorporation and dissolution dates, and sometimes shareholders. Track **people across companies**: one director appearing in twenty short-lived firms is a pattern.",
                    "**Shell companies** hide owners behind nominee directors, registered agents and addresses shared by hundreds of firms. A registered address that's a mailbox service or a formation agent is a flag, not proof of wrongdoing.",
                    "Leaks and investigations add hidden layers: the ICIJ Offshore Leaks database and sanctions lists (OpenSanctions) connect names to offshore structures and designated persons."
                ],
                "steps": [
                    "Search the company in its national registry and OpenCorporates.",
                    "List directors, addresses and key dates.",
                    "Search each director for other companies.",
                    "Check offshore leaks and sanctions lists for names and addresses."
                ],
                "tools": ["opencorporates", "companieshouse", "edgar", "offshoreleaks", "opensanctions"],
                "field_note": "Follow the people, not the company names. Companies are disposable; directors repeat.",
                "quiz": [
                    {"q": "Which resource searches company records across many jurisdictions?",
                     "options": ["OpenCorporates", "SunCalc", "Mapillary", "TinEye"],
                     "answer": 0, "why": "OpenCorporates aggregates registry data from 100+ jurisdictions."},
                    {"q": "A company's registered address is shared by 400 other firms. This means...",
                     "options": ["It's definitely a crime", "It's likely a formation agent or mailbox address: a flag worth noting", "It's a big office tower, nothing to see", "The registry is broken"],
                     "answer": 1, "why": "It's common for legitimate small firms too; note it and keep digging."},
                    {"q": "Why track directors across companies?",
                     "options": ["Directors repeat across firms, revealing networks", "Company names never change", "It's faster than reading", "Registries require it"],
                     "answer": 0, "why": "Names of companies change easily; the people behind them tend to recur."}
                ]
            },
            {
                "id": "m7l2", "title": "Domains and infrastructure", "minutes": 8,
                "summary": "WHOIS, DNS, certificates and the tracking codes that link websites together.",
                "body": [
                    "Every domain has a registration record. **WHOIS/RDAP** shows the registrar, creation date and sometimes the owner, though privacy services now hide most owners. **Historical WHOIS** services keep records from before privacy was switched on.",
                    "A **creation date** is a quick truth test: a shop claiming 'since 1998' on a domain registered three weeks ago is lying about something.",
                    "**DNS** records, reverse-IP lookups and **certificate transparency** logs (crt.sh) reveal other domains and subdomains on the same infrastructure. URLScan shows what a page loads and where it's hosted.",
                    "Shared **tracking IDs** are the classic pivot: analytics and advertising codes (for example Google Analytics or AdSense IDs) are tied to one account. Two websites using the same code are almost certainly run by the same person or company. Search the ID itself."
                ],
                "steps": [
                    "Look up WHOIS: registrar, creation date, name servers.",
                    "Check historical WHOIS for owner details before privacy.",
                    "Search certificate logs and reverse IP for related domains.",
                    "Pull tracking IDs from the page source and search them."
                ],
                "tools": ["viewdns", "crtsh", "urlscan", "dnsdumpster"],
                "field_note": "View source (Ctrl+U) and search for 'UA-', 'G-' and 'pub-': tracking IDs link sites.",
                "quiz": [
                    {"q": "A shop says 'trusted since 1998', but its domain was registered last month. This is...",
                     "options": ["Normal", "A red flag that its claims are false", "Proof it's a government site", "Irrelevant"],
                     "answer": 1, "why": "The creation date contradicts the claim. Many fake shops are weeks old."},
                    {"q": "Two websites share the same analytics tracking ID. This suggests...",
                     "options": ["Nothing", "They're likely run by the same person or organisation", "They're both hacked", "They're in the same country"],
                     "answer": 1, "why": "Tracking IDs belong to one account, so sharing one links the sites."},
                    {"q": "WHOIS shows 'REDACTED FOR PRIVACY'. Where might the owner still appear?",
                     "options": ["Historical WHOIS records from before privacy was turned on", "The domain's favicon", "Nowhere ever", "The URL's length"],
                     "answer": 0, "why": "Historical WHOIS keeps older records, often with real owner details."}
                ]
            },
            {
                "id": "m7l3", "title": "Following assets", "minutes": 7,
                "summary": "Property, vehicles, liens and judgments: legally tracing what someone owns.",
                "body": [
                    "Asset searches support debt recovery, divorce settlements and fraud cases. Sources include **property records** (deeds, mortgages, sales), **liens and UCC filings** (security interests in business assets in the US), court **judgments**, bankruptcy filings, and company ownership.",
                    "Vehicle and vessel records are more restricted. In the US, the Driver's Privacy Protection Act limits access to motor-vehicle records to permissible purposes; aircraft and ship registries are more open. Flight and ship trackers show movements of planes and yachts by registration.",
                    "Lifestyle clues on social media (a new boat, a holiday home) point you toward records to check, but they are not proof of ownership.",
                    "Bank account details are not public. Obtaining them by pretexting is illegal; they come through court processes (subpoenas, discovery) handled by lawyers."
                ],
                "steps": [
                    "Search property records in every county or region linked to the subject.",
                    "Search liens, judgments and bankruptcy filings.",
                    "Check company ownership for assets held through firms.",
                    "Note lifestyle clues and verify them against registries."
                ],
                "tools": ["opencorporates", "courtlistener", "flightradar", "marinetraffic"],
                "field_note": "Rich people rarely own things in their own name. Check their companies, trusts and spouses' names.",
                "quiz": [
                    {"q": "How are bank account details legally obtained in a civil case?",
                     "options": ["By pretexting the bank", "Through court processes like subpoenas, handled by lawyers", "From social media", "By guessing"],
                     "answer": 1, "why": "Financial records come through legal process. Pretexting for them is a crime in many places."},
                    {"q": "Your subject posts photos of a yacht. This proves...",
                     "options": ["They own it", "Nothing yet: it's a lead to check against registries", "They're a sailor", "They're rich"],
                     "answer": 1, "why": "They might have rented it or been a guest. Verify ownership in records."},
                    {"q": "Assets are often held...",
                     "options": ["Only in the person's own name", "Through companies, trusts or relatives", "In public bank lists", "On social media"],
                     "answer": 1, "why": "Check corporate and family structures."}
                ]
            }
        ]
    },
    {
        "id": "m8", "num": 8, "title": "Going Pro: The PI Business", "tag": "Career", "icon": "award",
        "blurb": "Licensing, verification, reporting and how to build a practice clients trust.",
        "lessons": [
            {
                "id": "m8l1", "title": "Licensing and the work itself", "minutes": 8,
                "summary": "What private investigators actually do, and what it takes to do it legally.",
                "body": [
                    "Most PI work is quiet and paper-heavy: **insurance claims** (is the injured claimant really bedridden?), **due diligence** on companies and executives, **skip tracing** (finding people who owe money or must be served court papers), litigation support for lawyers, fraud, missing persons, intellectual-property cases and background research.",
                    "Many jurisdictions require a **licence** to investigate for pay. Requirements vary: some US states require years of supervised experience (California, for example, asks for thousands of hours), exams, background checks, fingerprints and insurance. In Canada, provinces such as Ontario require training and an exam; Québec has its own regulator. Some countries have no specific licence but still apply data-protection law. Always check your regulator's current rules: they change.",
                    "Working for a licensed agency first is the classic path: you learn surveillance, report writing and court procedure under supervision while you log qualifying hours.",
                    "OSINT is now central to the job. Agencies hire analysts who can do in an afternoon online what used to take a week of field work."
                ],
                "steps": [
                    "Find your regulator and read the current licence requirements.",
                    "List the experience, training and exam you need.",
                    "Look for agencies hiring junior investigators or OSINT analysts.",
                    "Start a portfolio of practice reports (fictional cases like the ones in Osinty count)."
                ],
                "tools": ["tracelabs"],
                "field_note": "Osinty's case files are practice. Your licence comes from your regulator, not from an app.",
                "quiz": [
                    {"q": "Which is typical private-investigator work?",
                     "options": ["Arresting suspects", "Insurance claim investigation and skip tracing", "Wiretapping phones", "Issuing search warrants"],
                     "answer": 1, "why": "PIs have no police powers; claims, due diligence and skip tracing are core work."},
                    {"q": "Licensing requirements for PIs...",
                     "options": ["Are identical everywhere", "Vary by jurisdiction; check your regulator's current rules", "Don't exist anywhere", "Only apply to police"],
                     "answer": 1, "why": "They differ by state, province and country, and change over time."},
                    {"q": "A classic way to gain qualifying experience is...",
                     "options": ["Working under a licensed agency", "Watching detective films", "Buying a badge online", "Starting with surveillance alone at night"],
                     "answer": 0, "why": "Supervised work at a licensed agency builds the hours and skills regulators require."}
                ]
            },
            {
                "id": "m8l2", "title": "Verification and grading sources", "minutes": 8,
                "summary": "How sure are you? The Admiralty code and the two-source rule.",
                "body": [
                    "Every fact in a report needs a **confidence**. The **Admiralty code** (NATO system) grades two things separately: the **source's reliability** from A (completely reliable) to F (cannot be judged), and the **information's credibility** from 1 (confirmed by other sources) to 6 (cannot be judged). A court record is usually 'A1'; an anonymous forum claim might be 'F3'.",
                    "The **two-source rule**: confirm important facts with at least two *independent* sources. Two websites copying the same press release are one source, not two.",
                    "Separate **facts** from **analysis**. 'The domain was registered on 2 September 2026 (WHOIS, A1)' is a fact. 'The shop is therefore likely fraudulent' is an assessment, and you should say how likely using consistent words (unlikely, likely, highly likely).",
                    "Actively look for evidence that you're wrong. Confirmation bias is the investigator's deadliest enemy."
                ],
                "steps": [
                    "Grade each source (A–F) and each piece of information (1–6).",
                    "Check that confirming sources are truly independent.",
                    "Label every statement as fact or assessment.",
                    "Write down the best alternative explanation and test it."
                ],
                "tools": ["grader"],
                "field_note": "Osinty's Casebook lets you grade every lead with the Admiralty code. Use it.",
                "quiz": [
                    {"q": "In the Admiralty code, what does 'B2' mean?",
                     "options": ["Usually reliable source, probably true information", "Bad source, false information", "Second page of results", "Bronze level"],
                     "answer": 0, "why": "B = usually reliable; 2 = probably true."},
                    {"q": "Two news sites print the same press release word for word. That's...",
                     "options": ["Two independent sources", "Effectively one source", "Three sources", "Proof"],
                     "answer": 1, "why": "Copies of one origin are not independent confirmation."},
                    {"q": "Which statement is an assessment rather than a fact?",
                     "options": ["The domain was registered on 2 Sept 2026", "The shop is likely fraudulent", "The registrar is CheapDNS", "The site loads tracking ID LX-447821"],
                     "answer": 1, "why": "'Likely fraudulent' is your judgement based on the facts."}
                ]
            },
            {
                "id": "m8l3", "title": "Reports and building your practice", "minutes": 7,
                "summary": "Write reports clients can act on, then grow a practice with a niche.",
                "body": [
                    "Lead with the answer: **BLUF** (bottom line up front). Then the scope (the question, dates, limits), the findings with sources and confidence, the methodology, and appendices with captures. Write plainly; a lawyer or a judge may read every word.",
                    "Keep the **chain of custody**: what you captured, when, how, and where it's stored. Never alter originals; work on copies.",
                    "Growing a practice: pick a **niche** (insurance, corporate due diligence, missing persons, brand protection), build relationships with lawyers and insurers, carry professional liability insurance, and use clear contracts that define scope, purpose and what you won't do.",
                    "Keep learning: OSINT tools change monthly. Communities like Trace Labs run ethical search-party events where volunteers find leads on real missing-persons cases for law enforcement: excellent practice that helps people."
                ],
                "steps": [
                    "Write a one-paragraph BLUF for your last practice case.",
                    "Organise findings with source and confidence for each.",
                    "Keep originals untouched and log every capture.",
                    "Choose a niche and list three people who could refer you work."
                ],
                "tools": ["tracelabs", "hunchly"],
                "field_note": "Use the Report tab in your Casebook: it builds a clean, printable report from your leads.",
                "quiz": [
                    {"q": "What does BLUF mean?",
                     "options": ["Bottom line up front", "Big leads, useful facts", "Basic legal use form", "Background, location, user, file"],
                     "answer": 0, "why": "Put the answer first; details follow."},
                    {"q": "Why keep a chain of custody?",
                     "options": ["To prove evidence wasn't altered and show how it was obtained", "To make reports longer", "It's only for police", "To bill more hours"],
                     "answer": 0, "why": "Courts and clients need to trust that evidence is authentic."},
                    {"q": "What is Trace Labs known for?",
                     "options": ["Selling spyware", "Ethical search-party events finding leads on missing-persons cases", "Hacking competitions against companies", "Printing badges"],
                     "answer": 1, "why": "Volunteers practise OSINT to help find missing people, passing leads to law enforcement."}
                ]
            }
        ]
    },
]

# Daily briefing tips, one a day (by day of the year).
TIPS = [
    ("Quote the exact name", "Put names in quotes and add a city or employer: \"Martin Kessler\" Saskatoon beats Martin Kessler every time."),
    ("Check the oldest copy", "In a reverse image search, sort by date. The first place a picture appeared is usually its source."),
    ("Capture before you analyse", "Archive the page, screenshot it with the URL and time, then think. Content vanishes."),
    ("Usernames repeat", "People reuse handles for years. One rare username can unlock a whole online life."),
    ("Follow the directors", "Companies are disposable; the people behind them recur. Search each director for other firms."),
    ("Text beats trees", "In geolocation, one readable shop sign is worth ten guesses about vegetation."),
    ("Shadows are clocks", "Know the place and north, and shadow direction gives you the time of day."),
    ("Domain age is a truth test", "A shop 'trusted since 1998' on a three-week-old domain is lying about something."),
    ("Two sources, independent", "Two sites copying the same press release are one source, not two."),
    ("Don't touch the subject", "Never like, follow or message during research. Observe only."),
    ("Ask for the original file", "Screenshots and forwarded photos lose metadata. Ask the client for the original."),
    ("Search in their language", "Translate your keywords and try local spellings of names."),
    ("Facts vs. assessments", "Label every sentence in a report: what you found, and what you think it means."),
    ("Tracking IDs link sites", "View source and look for analytics and ad IDs. Shared IDs mean a shared owner."),
    ("Mind the namesakes", "Anchor every identification to two independent details: birth year, middle initial, past address."),
    ("Bracket the date", "A photo can't be newer than its first upload. Use that as your upper limit."),
    ("Friends' windows", "Private profile? The subject often appears in friends' and clubs' public photos."),
    ("Write the question first", "One sentence you could answer with a fact. Everything else is scope creep."),
    ("Mirror and crop", "Scammers flip stolen photos. Try a mirrored version and crop to the face."),
    ("Legal is the floor", "Before you dig, ask: is the purpose legitimate and the depth proportionate?"),
    ("Log everything", "Time, query, source, result. Your log is your memory and your defence."),
]


def all_lessons():
    for m in MODULES:
        for i, lesson in enumerate(m["lessons"]):
            yield m, i, lesson


def lesson_by_id(lesson_id):
    for m, i, lesson in all_lessons():
        if lesson["id"] == lesson_id:
            return m, i, lesson
    return None, None, None
