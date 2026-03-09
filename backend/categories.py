"""
categories.py — ClauseGuard Risk Category Definitions

v3 — 7 categories. Patterns sourced from reading real ToS documents:
     TikTok, Google, Meta, Spotify, Uber, Reddit, Snapchat, LinkedIn,
     Discord, FaceApp, Amazon, Apple.

Key additions in v3:
  - New category: content_rights (perpetual content licenses — completely
    missing from v2 despite being in virtually every ToS)
  - Expanded tracking_profiling with biometric collection, AI prompt logging,
    in-app browser surveillance, unsent message collection
  - Expanded data_sharing with sensitive personal information sharing patterns
  - Tightened negation-safe patterns throughout
"""

CATEGORIES: dict = {

    # ─── DATA SHARING ─────────────────────────────────────────────────────────
    "data_sharing": {
        "label": "Data Sharing",
        "description": "Clauses authorizing sharing of user data with third parties",
        "weight": 0.22,
        "rules": {
            "HIGH": [
                # Explicit sale language
                "sell your data",
                "sell your information",
                "sell personal data",
                "sell user data",
                "sell to third parties",
                "sale of personal information",
                "data broker",
                # Advertising-specific sharing
                "share with advertisers",
                "provide to advertisers",
                "share your data with advertisers",
                "advertising partners, data providers",
                "data providers, and analytics providers",
                "share for advertising purposes",
                "share for marketing purposes",
                "share with content providers for marketing",
                "registration data with",
                # Sensitive data sharing — these are HIGH because the data type is sensitive
                "racial or ethnic origin",
                "national origin",
                "religious beliefs",
                "mental or physical health diagnosis",
                "sexual life or sexual orientation",
                "sexual orientation",
                "status as transgender",
                "citizenship or immigration status",
                "financial information",
                "precise geolocation",
                "sensitive personal information",
                "biometric data",
                # Monetization
                "monetize your data",
                "monetize your information",
                "commercial partnerships",
                "leverage your information",
                "leverage personal data",
                # Merger / acquisition — data sold with the company
                "disclosed to third parties in connection with a corporate transaction",
                "merger, sale of assets",
                "acquisition of all or a portion",
                "reorganization, financing",
                "in the event of a sale",
                "transfer in connection with",
                # Cross-context behavioral advertising
                "cross-context behavioral advertising",
                "share your personal information with third parties for purposes of",
            ],
            "MEDIUM": [
                # Standard "we share with partners" language
                "share with third parties",
                "share with our partners",
                "share with affiliates",
                "share with business partners",
                "share with select third parties",
                "share with trusted third parties",
                "share your information with",
                "share personal data",
                "share information about you",
                "disclose to third parties",
                "disclose personal information",
                "disclose your information",
                "transfer to third parties",
                "transfer your data",
                "provide to third parties",
                "provide to our partners",
                "share with members of our corporate group",
                "entities within our corporate group",
                "share with subsidiaries",
                "affiliates and subsidiaries",
                # Measurement / analytics sharing
                "share with measurement partners",
                "share data with service providers to help our advertisers",
                "measure the effectiveness of their ads",
                "measure the effectiveness of advertising",
                # Collection about you from third parties (they buy your data)
                "collect information about you from third-party services",
                "receive information about you from",
                "information about you from others",
                "information provided to us by third parties",
                # Contact syncing — accessing your address book
                "sync your contacts",
                "collect information from your device's phone book",
                "friends list from your social network",
                "match that information to users",
                # Business purposes catch-all
                "for business purposes",
                "for commercial purposes",
                "necessary to perform business operations",
            ],
            "LOW": [
                "share with service providers",
                "share with vendors",
                "share aggregated data",
                "share anonymized data",
                "share non-personal information",
                "share de-identified",
                "aggregate or de-identify",
                "share with payment providers",
                "share with identity verification",
                "share with cloud hosting",
            ],
        },
    },

    # ─── TRACKING & PROFILING ─────────────────────────────────────────────────
    "tracking_profiling": {
        "label": "Tracking & Profiling",
        "description": "Clauses enabling behavioral tracking, biometric collection, or user profiling",
        "weight": 0.20,
        "rules": {
            "HIGH": [
                # Biometric collection — faces, fingerprints, voice (HIGH: irreversible)
                "face id",
                "fingerprint id",
                "facial recognition",
                "facial, body or voice information",
                "face and other body parts",
                "biometric information",
                "biometric identifiers",
                "voiceprint",
                "retina or iris scan",
                "uniquely identifying a person",
                "face scan",
                # Surveillance-level collection
                "collect all content you compose, send, or receive",
                "content you compose, send, or receive",
                "messages you compose but do not send",
                "regardless of whether you choose to save or publish",
                "pre-uploading at the time of creation",
                "collect information about your interactions with websites when you use our in-app browser",
                "in-app browser",
                # AI prompt / interaction logging
                "ai interactions, including prompts",
                "prompts, questions, files, and other types of information that you submit",
                "responses they generate",
                # Cross-site / cross-app tracking
                "behavioral profiling",
                "cross-site tracking",
                "track across websites",
                "track across apps",
                "track your activity across",
                "track you across",
                "activities on other websites and apps",
                "actions outside of the platform",
                "actions you have taken outside",
                # Identity matching across devices/sites
                "match you and your actions",
                "mobile identifiers for advertising",
                "hashed email addresses and phone numbers",
                "cookie identifiers",
                "device fingerprinting",
                "fingerprint your device",
                "persistent identifier",
                # Device hardware identifiers — harder to change than cookies
                "mac addresses",
                "imei",
                "sim serial number",
                "hardware serial number",
                # Collection even without account
                "even if you are not a user",
                "even if you do not have an account",
                # Clipboard access
                "clipboard content",
                "accessed through your device's clipboard",
                "access clipboard",
                # Building profiles
                "build a profile",
                "build a detailed profile",
                "infer sensitive attributes",
                "infer information about you",
                "assign an age range and gender",
                "infer age range and gender",
            ],
            "MEDIUM": [
                # Targeted advertising
                "personalized advertising",
                "targeted advertising",
                "behavioral advertising",
                "interest-based advertising",
                "serve you personalized ads",
                "advertising partners",
                "analytics partners",
                "measurement and analytics services",
                # Standard tracking tech
                "track your usage",
                "track your activity",
                "web beacons",
                "pixel tags",
                "tracking technologies",
                "track clicks",
                "track purchases",
                "browsing history",
                "search history",
                # Profiling via content analysis
                "content characteristics and features",
                "identifying objects and scenery",
                "existence and location of a face",
                "nature of the audio",
                "text of words spoken",
                # Location tracking
                "precise location",
                "gps",
                "cell tower information",
                "public wi-fi hotspots",
                "approximate location",
                "location information from your device",
                # Personalization (profiling presented as a feature)
                "personalize your experience",
                "personalized recommendations",
                "personalized content",
                # Keystroke / interaction logging
                "duration and frequency of your use",
                "engagement with other users",
                "how you interact with content and ads",
            ],
            "LOW": [
                "use cookies",
                "analytics",
                "log files",
                "session data",
                "usage data",
                "improve our services",
                "remember your preferences",
                "ip address",
                "device identifier",
                "access dates and times",
                "server logs",
                "time zone settings",
                "language settings",
                "operating system",
            ],
        },
    },

    # ─── THIRD-PARTY ACCESS ───────────────────────────────────────────────────
    "third_party_access": {
        "label": "Third-Party Access",
        "description": "Clauses granting third parties access to user data or accounts",
        "weight": 0.13,
        "rules": {
            "HIGH": [
                # Government / law enforcement access
                "law enforcement agencies, public authorities",
                "government access",
                "law enforcement access without notice",
                "national security",
                "intelligence agencies",
                "government requests",
                "authorities or regulators",
                "law enforcement, governmental",
                # "Good faith belief" — no warrant needed
                "good faith belief",
                "if we have good faith belief",
                "if we believe it is necessary",
                "if we reasonably believe",
                # Broad access grants
                "grant third parties access",
                "third parties may access your",
                "allow third parties to collect",
                "third-party access to your account",
                # Corporate group = data flows within conglomerate freely
                "entities within our corporate group",
                "members of our corporate group",
                "corporate group processes",
                # Collection by others mentioning you
                "information about you from others",
                "included or mentioned in user content",
                "contact information is provided to us",
                # Foreign government access risk
                "transfer to countries outside",
                "international transfer",
                "cross-border transfer of data",
            ],
            "MEDIUM": [
                "third-party services",
                "integrated services",
                "third-party applications",
                "access by third parties",
                "partners may access",
                "third party may collect",
                "third-party providers",
                "business partners may",
                "link your account to a third-party",
                "third parties whose platforms are integrated",
                "sign-up or log-in using a third-party service",
                # Compliance sharing
                "tax authorities",
                "regulatory authorities",
                "public authorities, such as tax",
                # Enforcement access
                "detect, investigate, and prevent",
                "investigate potential violations",
                "enforce our terms",
                "protect the rights, property",
                "copyright holders",
            ],
            "LOW": [
                "third-party links",
                "external websites",
                "third-party content",
                "linked services",
                "third-party platforms",
            ],
        },
    },

    # ─── DATA RETENTION ───────────────────────────────────────────────────────
    "data_retention": {
        "label": "Data Retention",
        "description": "Clauses specifying how long user data is kept",
        "weight": 0.13,
        "rules": {
            "HIGH": [
                "retain indefinitely",
                "retain forever",
                "no obligation to delete",
                "cannot guarantee deletion",
                "backup copies may be retained",
                "retain after account deletion",
                "retain after termination indefinitely",
                "no deletion guarantee",
                # Even non-users have data retained
                "even if you are not a user, information about you",
                "may not stop from getting and collecting data",
                # Collecting before you decide to publish
                "regardless of whether you choose to save or publish",
            ],
            "MEDIUM": [
                # The "as long as necessary" language — vague by design
                "retain for as long as necessary",
                "retain as long as necessary to provide",
                "as long as necessary to provide the services",
                "for as long as necessary",
                # Retention after closure
                "retain after account closure",
                "backup copies may persist",
                "retain for business purposes",
                "may retain your data",
                "retain for an extended period",
                "stored even after deletion",
                # "Legitimate interest" defined by them
                "legitimate business interest",
                "legitimate interests",
                # Safety/stability as retention justification
                "safety, security and stability",
                "enhancing its safety",
                "improving and developing the services",
                # Legal defense — they keep data in case you sue
                "exercise or defense of legal claims",
                "for the exercise or defense",
                "comply with legal obligations",
                "comply with contractual and legal obligations",
                # Derived data persists
                "derived data may be retained",
                "anonymized data may be retained",
                "aggregated data may be retained",
            ],
            "LOW": [
                "retain as required by law",
                "retain for legal obligations",
                "retain for a limited period",
                "deleted upon request",
                "retention policy",
                "deleted and not retained",
            ],
        },
    },

    # ─── ARBITRATION ──────────────────────────────────────────────────────────
    "arbitration": {
        "label": "Arbitration & Dispute Resolution",
        "description": "Clauses limiting user rights through mandatory arbitration",
        "weight": 0.13,
        "rules": {
            "HIGH": [
                # Explicit jury/court waivers
                "waive your right to a jury trial",
                "waive right to jury",
                "waiving their respective rights to a trial by jury",
                "waive any right to a jury",
                "right to a trial by jury",
                "there is no judge or jury in arbitration",
                "less discovery and appellate review than in court",
                # Class action waivers
                "class action waiver",
                "waive right to class action",
                "waive the right to participate in a class",
                "no class arbitration",
                "not as a plaintiff or class member",
                "or class actions of any kind",
                "individual basis to resolve disputes",
                "only in your individual capacity",
                # Binding mandatory language
                "binding arbitration",
                "mandatory binding individual arbitration",
                "mandatory arbitration provision",
                "this agreement contains a mandatory arbitration",
                "requires the use of arbitration",
                "rather than jury trials",
                "you give up your right",
                "you are waiving",
                "you waive any right",
            ],
            "MEDIUM": [
                "mandatory arbitration",
                "disputes resolved by arbitration",
                "arbitration agreement",
                "submit to arbitration",
                "resolve disputes through arbitration",
                "arbitration shall be final",
                "will be determined by mandatory",
                "arbitration is more informal than a lawsuit",
                "federal arbitration act",
                "consumer arbitration rules",
                "american arbitration association",
                "AAA rules",
                "jams rules",
                "informal dispute resolution",
                "30-day notice period before arbitration",
            ],
            "LOW": [
                "alternative dispute resolution",
                "mediation",
                "governing law",
                "jurisdiction",
                "small claims court",
                "dispute resolution",
                "applicable law",
            ],
        },
    },

    # ─── LIABILITY LIMITATION ─────────────────────────────────────────────────
    "liability_limitation": {
        "label": "Liability Limitation",
        "description": "Clauses limiting the company's legal liability to the user",
        "weight": 0.09,
        "rules": {
            "HIGH": [
                "not liable for any damages",
                "disclaim all liability",
                "no warranty of any kind",
                "disclaim all warranties",
                "in no event shall",
                "exclude all liability",
                "maximum liability shall not exceed",
                "not liable for any loss",
                # Full disclaimer language
                "make no warranties, express or implied",
                "no warranties, express or implied",
                "express or implied warranty",
                "express or implied, with respect to",
                # Caps on what they owe you
                "your sole remedy",
                "our sole liability shall be",
                "sole remedy, and our sole liability",
                # The "fullest extent" catch-all
                "to the fullest extent permitted by applicable law",
                "fullest extent permitted",
                "to the fullest extent",
                # Security not guaranteed
                "100 percent secure",
                "cannot be guaranteed to be 100",
                "no data storage system",
                "transmission of data over the internet",
            ],
            "MEDIUM": [
                "limit our liability",
                "not responsible for any loss",
                "provided as is",
                "provided as-is",
                "as is and as available",
                "without warranty",
                "we do not warrant",
                "we make no representations",
                "no guarantees",
                "fitness for a particular purpose",
                "merchantability",
                "we are not responsible for",
                "we cannot guarantee",
                "we do not guarantee",
            ],
            "LOW": [
                "liability limited to fees paid",
                "to the extent permitted by law",
                "some jurisdictions do not allow",
                "limitation of liability",
                "certain state laws do not allow",
            ],
        },
    },

    # ─── CONTENT RIGHTS ───────────────────────────────────────────────────────
    # NEW in v3. One of the most overlooked but universal risks.
    # Every major platform (Instagram, TikTok, Snapchat, YouTube, Reddit,
    # LinkedIn) takes a broad license on everything you post. This license is:
    #   - Perpetual (never expires, even after you delete it)
    #   - Irrevocable (you can't take it back)
    #   - Royalty-free (they don't pay you)
    #   - Sublicensable (they can give it to others)
    #   - Worldwide (including jurisdictions with weak privacy law)
    #   - For any purpose including commercial use
    # Most users have no idea they've signed this away.
    # ─────────────────────────────────────────────────────────────────────────
    "content_rights": {
        "label": "Content & IP Rights",
        "description": "Clauses granting the company broad rights over your content",
        "weight": 0.10,
        "rules": {
            "HIGH": [
                # The full perpetual license stack
                "perpetual, irrevocable",
                "irrevocable, nonexclusive, royalty-free",
                "perpetual, royalty-free",
                "royalty-free, worldwide",
                "sublicensable license",
                "transferable sub-licensable license",
                "throughout the universe in perpetuity",
                "in any and all media, now known or hereafter devised",
                # Commercial use of your likeness
                "commercial purposes",
                "you will not be entitled to any compensation",
                "without compensation to you",
                "use your name, likeness",
                "use your name, image",
                "use your voice",
                # AI training on your content
                "train artificial intelligence",
                "train ai models",
                "train machine learning",
                "use your content to train",
                "use for machine learning",
                "use content for research and development",
                "use to improve our ai",
            ],
            "MEDIUM": [
                # Standard content license (necessary but still worth flagging)
                "grant us a license",
                "you grant a license",
                "license to use your content",
                "worldwide license",
                "non-exclusive license",
                "royalty-free license",
                "right to use, reproduce",
                "right to display your content",
                "right to distribute your content",
                "right to create derivative works",
                "right to modify your content",
                "promote, exhibit, broadcast",
                "publicly perform and publicly display",
                "in connection with the platform",
                # Derivative works — they can remix your content
                "create derivative works from",
                "derivative works based on",
                "adapt or modify",
            ],
            "LOW": [
                # Hosting license — genuinely needed to operate the service
                "solely for the purpose of operating",
                "solely to provide the service",
                "limited license to host",
                "as necessary to provide",
                "in order to provide the services",
            ],
        },
    },
}

# Numeric ordering for risk level comparison
RISK_LEVEL_ORDER: dict[str, int] = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

# Base score contribution for each risk level
RISK_LEVEL_SCORES: dict[str, int] = {"LOW": 25, "MEDIUM": 60, "HIGH": 100}
