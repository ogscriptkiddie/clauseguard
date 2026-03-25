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
                "data resellers",
                "data reseller",
                # Advertising-specific sharing
                "share with advertisers",
                "provide to advertisers",
                "share your data with advertisers",
                "advertising partners, data providers",
                # Spotify: receiving inferences from ad/marketing partners (spotify)
                "receive inferences from certain advertising or marketing partners",
                "partners understanding of your interests and preferences",
                "inferences are the partners understanding",
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
                # Spotify: explicit business sale transfer
                "negotiate to sell our business to a buyer or possible buyer",
                "sell or negotiate to sell our business",
                "transfer your personal data to a successor or affiliate",
                "acquisition of all or a portion",
                "reorganization, financing",
                "in the event of a sale",
                "transfer in connection with",
                # Human annotation: law enforcement sharing is HIGH (meta_021, meta_030)
                "access, preserve, use and share your information in response to legal",
                "access, preserve, use and share your information in response to",
                "we will access, preserve and share your information with regulators",
                "share your information with law enforcement",
                # Human annotation: global cross-border transfer is HIGH (meta_029)
                "share information we collect globally, both internally",
                "transferring or enabling access to your data globally",
                "processing your information across borders",
                # Spotify: explicit weaker protection warning
                "countries whose data protection laws are not considered to be as strong",
                "data protection laws are not considered to be as strong as eu laws",
                "they may not give you the same rights over your data",
                "shares personal data internationally with",
                # Apple: personal data transferred to entities around the world
                "may be transferred to or accessed by entities around the world",
                "transferred to or accessed by entities around the world",
                "process user data globally",
                "processed, transferred, and stored in the u.s. and other countries",
                "different data protection standards may apply",
                "you may not have the same rights as you do under local law",
                "by accessing or using our services or otherwise providing information to us, you understand",
                # Cross-context behavioral advertising
                "cross-context behavioral advertising",
                "share your personal information with third parties for purposes of",
            ],
            "MEDIUM": [
                # Standard "we share with partners" language
                "share with third parties",
                "share with our partners",
                "share with affiliates",
                "share information between and among",
                "between and among reddit, and any of our parents, affiliates",
                "parents, affiliates, subsidiaries",
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
                "provide information to our related companies",
                "related companies, including parents, affiliates, subsidiaries",
                # Spotify: all data categories shared with group + acquired companies (spotify_017)
                "including companies that spotify acquires",
                # LinkedIn: affiliates include Microsoft and Github (broad)
                "linkedin ireland, linkedin corporation, linkedin singapore and microsoft corporation",
                "microsoft corporation or any of its subsidiaries",
                "including microsoft and github",
                "group companies, including companies that spotify acquires",
                "sharing data with our measurement companies",
                "sharing data with our podcast companies",
                "other companies under common control and ownership",
                "affiliates and subsidiaries",
                # Measurement / analytics sharing
                "share with measurement partners",
                "share data with service providers to help our advertisers",
                "measure the effectiveness of their ads",
                "measure the effectiveness of advertising",
                # Collection about you from third parties (they buy your data)
                "collect information about you from third-party services",
                "receive information about you from",
                "third-party data providers, such as demographic information",
                "receive information about you from advertisers and third-party data providers",
                "how you engage with other products and services outside of discord",
                "information about you from others",
                "information provided to us by third parties",
                # Contact syncing — accessing your address book
                "sync your contacts",
                "collect information from your device's phone book",
                "friends list from your social network",
                "match that information to users",
                # Business purposes catch-all
                "for business purposes",
                # Spotify: pseudonymised data shared under contract
                "provide pseudonymised data about our users",
                "pseudonymised data about our users listening",
                "fulfil contractual obligations with third parties",
                "for commercial purposes",
                "necessary to perform business operations",
                # Meta cross-product / cross-company sharing
                "use information across our products",
                "cross app interactions",
                "cross-app interactions",
                "enable cross app interactions",
                "information across the meta company products",
                "share information we collect globally",
                "internally across our offices and data centers",
                "externally with our partners, vendors and service providers",
                "insights and measurement reports to businesses, advertisers",
                "understand the kinds of people who are seeing their content and ads",
                "how their content and ads are performing on and off",
            ],
            "LOW": [
                "share with service providers",
                "share with vendors",
                "share aggregated data",
                "share aggregated user statistics in order to describe",
                "aggregated or anonymized such that it cannot reasonably be used to identify you",
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
                "generating transcriptions of content as part of our investigation",
                "proactively scanning attachments and other content",
                "scanning attachments",
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
                # Reddit annotation: ad measurement providers get cookie IDs, IP, hashed email (reddit_029)
                "cookie ids, your ip address, and a hashed version of your email",
                "cookie ids, your ip address",
                "hashed version of your email",
                "these third parties may combine that information with other information they already have about you",
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
                # Spotify: detailed behavioral data collection is HIGH (spotify_003)
                "streaming history",
                # Apple: usage data to power services = LOW (internal purpose)
                "collect data on what songs you play in order to provide you with the content",
                "collect data on what songs you play",
                "search queries",
                "inferences of your age, interests and preferences based on your usage",
                "inferences of your age, interests",
                "browsing history",
                "listening history",
                # Human annotation: using sensitive attributes for personalisation is HIGH (meta_009)
                "use health, financial, political",
                "use sensitive information to personalize",
                "sensitive information you choose to provide to personali",
                "use health information to personalize",
                "assign an age range and gender",
                "infer age range and gender",
                "infer attributes such as age range",
                "we infer attributes",
                "infer your age",
                # Discord annotation: receiving info about you from actions on other sites (discord_010)
                "take certain actions on other sites, we may receive information about you",
                "receive information about you from other sites",
                "we may receive information about you",
                "when you take certain actions on other sites",
                "actions on other sites",
                # Microsoft Xbox: gameplay tracked and shared with game devs/publishers (microsoft_tos)
                "information about your game play, activities and usage of games and xbox services will be tracked and shared",
                "tracked and shared with applicable third parties, including game developers and publishers",
                "information about your game play, activities and usage of games and xbox services will be tracked and shared with applicable third parties",
                # Meta Audience Network and off-platform tracking
                "identify you as a meta product user",
                "information from third parties to tailor the ads you see",
                "activity off meta company products that we have associated with you",
                "we receive this information whether or not you are logged in",
                "we receive this information whether or not you're logged in",
                "personalize ads that we show you through",
                "when you visit other apps",
                "tailor the ads you see",
            ],
            "MEDIUM": [
                # Targeted advertising
                "personalized advertising",
                "targeted advertising",
                "behavioral advertising",
                "interest-based advertising",
                "serve you personalized ads",
                "surface sponsored content",
                "deliver relevant sponsored content",
                "sponsored content that may be of interest to you",
                "sponsored formats that may be of interest",
                "advertising partners",
                # Spotify: ad partners combining your data with their own (spotify_015/016)
                "our partners may also combine the personal data we share with them with other data they collect about you",
                "combine the personal data we share with them with other data",
                "combine spotify data with other data they already hold",
                "analytics partners",
                "audience measurement",
                "perform audience measurement",
                "partner with service providers that perform audience measurement",
                "demographic information about the population",
                "measurement and analytics services",
                # Standard tracking tech
                "track your usage",
                "track your activity",
                # Reddit annotation: behavioral action tracking (reddit_008)
                "information about the actions you take when using the services",
                "interactions with the platform and content, like voting, saving, hiding",
                "interactions with communities, like your subscriptions",
                "web beacons",
                "pixel tags",
                "tracking technologies",
                "track clicks",
                "track purchases",
                "browsing history",
                "search history",
                # Reddit annotation: detailed usage including ad interaction tracking (reddit_011)
                "pages visited, how you interact with content, ads, and communities",
                "upvotes and downvotes, links clicked",
                "interact with content, ads",
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
                "customize your experience",
                "customizing your experience",
                "customizing your experience on discord",
                "customize your experience on discord",
                "personalized recommendations",
                # Google: automated systems analyze content for profiling/personalization (google_005 HIGH)
                "using automated systems and algorithms to analyze your content",
                "to customize our services for you, such as providing recommendations and personalized search results, content, and ads",
                "recognize patterns in data",
                # LinkedIn: data used for recommendations + ad targeting (linkedin_tos_006/016)
                "make recommendations for connections, content, ads, and features",
                "organize content in your feed",
                "recommend jobs to you and you to recruiters",
                # Spotify: ML training for personalisation = tracking MEDIUM (spotify_008)
                "development and training of algorithmic and machine learning models",
                "improve our personalised recommendation algorithms",
                # Apple: Applebot web crawler as AI training source
                "apple uses applebot, a web crawler, to crawl information that is publicly available",
                "as a source for our foundational ai models",
                "build ai features",
                # Google: AI-generated content cannot develop competing ML models (google_tos)
                "using ai-generated content from our services to develop machine learning models",
                "ai-generated content from our services to develop machine learning models or related ai technology",
                # Amazon: prohibition on using AI output to train competing models
                "use ai-generated content from the amazon services to, directly or indirectly, develop",
                "develop or improve large language or multimodal models",
                # Microsoft: broad content license to use/transmit/display content (ms_002 HIGH)
                "to make copies of, retain, transmit, reformat, display, and distribute via communication tools",
                "distribute via communication tools your content on the services",
                "your content may appear in demonstrations or materials that promote the service",
                # Microsoft: AI services data cannot be used to train any AI (microsoft_tos)
                "data from the ai services, to create, train, or improve",
                "create, train, or improve directly or indirectly any ai technology",
                "you may not use the ai services, or data from the ai services, to create",
                # Human annotation: missed personalisation language (meta_004, meta_010)
                "provide a personalized experience",
                "provide personalized experience",
                "personalize features, content and ads",
                "personalize features, content, and ads",
                "personalize the ads people see",
                "select interests during account creation",
                "to help generate content and community recommendations or select more relevant advertising",
                "select more relevant advertising",
                "personalized features and content",
                "personalize features and content",
                "personalizing features and content",
                "personalize features, content",
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
                # Spotify: online identifiers used for targeting = MEDIUM (spotify_004)
                "online identifiers such as cookie data and ip addresses",
                "online identifiers such as",
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
                "third-party developers to build certain features",
                # Microsoft: third-party apps may store your content/data (ms_011 HIGH)
                "the third-party apps and services may allow or require you to store your content or data with the publisher",
                "allow or require you to store your content or data with the publisher",
                # Microsoft: work/school account employer can access comms/files (microsoft_tos)
                "owner of the domain associated with your email address may",
                "control and administer your account, and access and process your data, including the contents of your communications and files",
                "access and process your data, including the contents of your communications",
                # Amazon: other businesses operating through their platform
                "parties other than amazon operate stores, provide services",
                "purchasing directly from those third parties, not from amazon",
                "allows other third parties to access reddit public content",
                "access public content and information using",
                "developer services, including",
                "apis, developer platform",
                "server administrators can add bots",
                "third-party games",
                "we don't control them or what information they collect",
                "third parties whose platforms are integrated",
                "sign-up or log-in using a third-party service",
                "integrated partners receive information about you and your activity",
                "integrated partners can always access information",
                # Uber annotation: sharing personal info with other users (uber_019)
                "shares your first name, profile photo, rating",
                "shares your name, profile photo",
                "location before and during trip",
                # Uber annotation: subsidiaries and affiliates sharing (uber_025)
                "share data with our subsidiaries and affiliates",
                "share data with subsidiaries and affiliates",
                # Uber-style AI vendor and social media sharing
                "service providers that provide us with artificial intelligence and machine learning",
                # Spotify ToS: business partners deliver ads via your device (spotify_tos_006)
                "allow our business partners to do the same",
                "to allow the spotify service to use the processor, bandwidth",
                "use the processor, bandwidth, and storage hardware on your device",
                "social media companies, including",
                "in connection with uber's use of their tools",
                "ad technology vendors, measurement and analytics providers",
                "ad networks and advertisers",
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
                # Spotify: streaming history kept for life of account (spotify_021)
                "keep streaming history for the life of an account",
                "kept for the life of the account",
                "for the life of an account",
                "retain forever",
                "no obligation to delete",
                "cannot guarantee deletion",
                "backup copies may be retained",
                "retain after account deletion",
                "retain after termination indefinitely",
                "no deletion guarantee",
                # Human annotation: open-ended discretionary retention is HIGH (meta_016)
                "on a case-by-case basis",
                "we decide how long we need information on a case-by-case",
                # Uber-style retention after ban
                "retain your data after an account deletion request to prevent you from re-obtaining access",
                # Spotify: extended retention after deletion for legal/investigation purposes
                "after your account is deleted, we keep some data for a longer time period",
                "keep some data for a longer time period but for very limited purposes",
                "mandatory data retention laws, government orders to preserve data",
                "government orders to preserve data relevant to an investigation",
                "account is suspended or banned, we may store the identifiers",
                "store the identifiers used to create the account",
                "to prevent you from creating new accounts",
                "if you are banned from",
                # Even non-users have data retained
                "even if you are not a user, information about you",
                "may not stop from getting and collecting data",
                # Collecting before you decide to publish
                "regardless of whether you choose to save or publish",
            ],
            "MEDIUM": [
                # The "as long as necessary" language — vague by design
                "retain for as long as necessary",
                # LinkedIn: no obligation to keep your content
                "linkedin is not a storage service",
                "no obligation to store, maintain or provide you a copy of any content",
                "until we determine it is no longer needed",
                "retain personal information until we determine",
                "retain as long as necessary to provide",
                "as long as necessary to provide the services",
                "for as long as necessary",
                # Retention after closure
                "retain after account closure",
                "backup copies may persist",
                # Discord: payment processors storing billing and bank info (discord_005)
                "payment processors receive and process your payment information",
                "receive and process your payment information",
                "receive and store certain billing information, including",
                "store certain billing information",
                "receive and store certain billing information",
                "bank account information to facilitate payments",
                # LinkedIn: storing and billing expired payment method
                "store and continue billing your payment method, even after it has expired",
                "billing your payment method, even after it has expired",
                "may automatically charge a secondary payment method",
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
                "establish, exercise, or defend legal claims",
                "to establish, exercise, or defend",
                "retain and use your information in connection with potential legal claims",
                "in connection with potential legal claims",
                "for the exercise or defense",
                "comply with legal obligations",
                "comply with contractual and legal obligations",
                # Derived data persists
                "derived data may be retained",
                # Human annotation: vague legitimate purposes and extended period (meta_019, meta_020)
                "if we need it for other legitimate purposes",
                "need it for other legitimate purposes",
                "other legitimate purposes",
                "for other legitimate purposes",
                "for an extended period of time",
                "keep information for an extended period",
                "extended amount of time",
                "extended period",
                "anonymized data may be retained",
                "aggregated data may be retained",
            ],
            "LOW": [
                "retain as required by law",
                "retain for legal obligations",
                "retain for a limited period",
                # Apple: explicit minimal retention commitment = LOW risk
                "work to retain the personal data for the shortest possible period permissible under law",
                # Apple: explicit intent to minimize retention = LOW
                "retain personal data only for so long as necessary to fulfill the purposes",
                "retain it only as long as necessary",
                "shortest possible period permissible under law",
                # Reddit annotation: ip addresses deleted after 100 days — retention LOW
                "delete any ip addresses collected after 100 days",
                "ip addresses collected after",
                "deleted upon request",
                "retention policy",
                "deleted and not retained",
                # Human annotation: standard operational and legal retention = LOW (meta_017, meta_018)
                "keep some of your information to maintain your account",
                "retain the information to comply with certain legal obligations",
                "how long we need to retain the information to comply",
                "necessary to comply with legal obligations",
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
                "court review of an arbitration award is limited",
                # Amazon: arbitration + court review limited in same sentence
                "there is no judge or jury in arbitration, and court review",
                "arbitrator can award on an individual basis the same damages",
                "more limited discovery than in court",
                "arbitrator may not award declaratory or injunctive relief",
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
                # Spotify ToS: time bar on claims
                "any claim arising under these terms must be commenced within one year",
                # Microsoft: one-year claim filing limit (microsoft_tos)
                "any claim related to these terms or the services must be filed in court or arbitration within one year",
                "must be filed in court or arbitration within one year",
                # Microsoft: permanent bar on claims after one year (ms_017 HIGH)
                "if not filed within that time, then it",
                "permanently barred",
                "if not filed within that time, then it's permanently barred",
                "no right to any remedy for any claim not asserted within that time period",
                "within one year after the date the party asserting the claim",
                "must be commenced by filing a demand for arbitration within one year",
            ],
            "LOW": [
                "alternative dispute resolution",
                "mediation",
                "governing law",
                "dispute jurisdiction",
                "exclusive jurisdiction",
                "small claims court",
                "governing dispute resolution",
                # LinkedIn: exclusive jurisdiction clause = arbitration/MEDIUM
                "all claims and disputes can be litigated only in the federal or state courts",
                # Google: California/Santa Clara exclusive forum selection (google_010 MEDIUM)
                "resolved exclusively in the federal or state courts of santa clara county",
                "california law will govern all disputes arising out of or relating to these terms",
                "you and linkedin each agree to personal jurisdiction in those courts",
                # Spotify ToS: asymmetric assignment rights
                "you may not assign these terms",
                "you may not assign these terms, in whole or in part",
                "dispute resolution process",
                "applicable arbitration law",
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
                # Spotify ToS full liability exclusion
                "in no event will spotify",
                "will not be liable for",
                "any indirect, special, incidental, punitive, exemplary, or consequential damages",
                "indirect, special, incidental, punitive",
                "aggregate liability for all claims",
                "aggregate liability for all claims relating to",
                # Google: liability capped at $500 or 125% of fees (google_tos)
                "google's total liability arising out of or relating to these terms is limited to the greater of",
                "limited to the greater of us$500 or 125% of the fees",
                "125% of the fees that you paid to use the relevant services in the 12 months before the breach",
                "google's total liability arising out of or relating to these terms is limited to the greater of",
                "125% of the fees that you paid to use the relevant services",
                # Apple: limits survive even remedy failure (apple_tos_009)
                "the foregoing limitations will apply even if the above stated remedy fails",
                "even if the above stated remedy fails of its essential purpose",
                # LinkedIn: explicit $1000 liability cap
                "will not be liable to you in connection with this contract for any amount that exceeds",
                "not be liable to you in connection with this contract for any amount that exceeds",
                "us $1000",
                # Microsoft: $10 liability cap for free services (microsoft_tos)
                "up to usd$10.00 if the services are free",
                "usd$10.00 if the services are free",
                "up to an amount equal to your services fee for the month during which the loss or breach occurred",
                "$1000",
                "disclaim all liability",
                "no warranty of any kind",
                "disclaim all warranties",
                "in no event shall",
                "exclude all liability",
                # Spotify ToS: indemnification clause (user holds company harmless)
                "indemnify and hold spotify harmless",
                # Apple: submit info at sole risk, releases Apple (apple_tos_014 - HIGH)
                "your submission of such information is at your sole risk",
                "hereby release apple from any and all liability",
                "release apple from any liability",
                "indemnify and hold harmless",
                "you agree to indemnify",
                "arising out of or related to your breach",
                "arising out of or related to any user content you post",
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
                # Spotify ToS: unilateral modification without liability
                "without liability to you",
                "may modify, suspend, or stop permanently or temporarily",
                # Apple: services can be interrupted/cancelled without guarantee (apple_tos_010)
                "apple may remove the services for indefinite periods of time",
                "cancel the services at any time, or otherwise limit or disable your access",
                "limit or disable your access to the services without notice to you",
                "may remove access to particular songs, videos, podcasts",
                "spotify has no obligation to provide a refund",
                "spotify has no liability to you, nor any obligation to provide a refund",
                "no guarantees",
                "fitness for a particular purpose",
                "merchantability",
                "we are not responsible for",
                # Spotify ToS: service changes without liability (spotify_tos_020)
                "may change from time to time and subject to applicable laws, without liability to you",
                "without liability to you",
                # Spotify ToS: no obligation to keep specific content (spotify_tos_023)
                "no obligation to provide any specific content",
                "spotify has no obligation to provide any specific content",
                # Apple: no obligation to keep even purchased content (apple_tos_012 - HIGH)
                "apple has no responsibility to continue making content available",
                "apple will not be liable to you if content, including purchased content, becomes unavailable",
                "including purchased content, becomes unavailable for download",
                "may remove access to particular songs, videos, podcasts",
                # Spotify ToS: no liability/refund for outages (spotify_tos_024)
                "no liability to you, nor any obligation to provide a refund",
                "in connection with internet or other service outages",
                # Spotify ToS: no liability after termination, no refunds (spotify_tos_025)
                "spotify shall, subject to applicable laws, have no liability or responsibility to you",
                "spotify will not refund any amounts that you have already paid",
                "we cannot guarantee",
                # Apple: no guarantee against hacking or security intrusion (apple_tos_015 - HIGH)
                "apple does not represent or guarantee that the services will be free from loss, corruption",
                "free from loss, corruption, attack, viruses, interference, hacking",
                "hereby release apple from any liability relating thereto",
                # Spotify ToS: price changes + no partial refunds (spotify_tos_028)
                "we do not provide refunds or credits for any partial subscription periods",
                "do not provide refunds or credits for any partial",
                "spotify may from time to time change the price",
                # Apple: right to modify/discontinue without notice or liability (apple_tos_019)
                "apple further reserves the right to modify, suspend, or discontinue the services",
                "apple will not be liable to you or to any third party should it exercise such rights",
                "we do not guarantee",
            ],
            "LOW": [
                "liability limited to fees paid",
                # Google: business users must indemnify Google (google_tos)
                "you'll indemnify google and its directors, officers, employees, and contractors",
                "for any third-party legal proceedings arising out of or relating to your unlawful use of the services",
                # Spotify ToS: sole remedy = stop using the service (spotify_tos_009)
                "your sole and exclusive remedy for any problems or dissatisfaction",
                "sole and exclusive remedy",
                # Google: narrows commitments, tells users not to rely for professional advice (google_019)
                "the only commitments we make about our services are provided in the warranty section",
                "don't rely on the services for medical, legal, financial, or other professional advice",
                "is to uninstall any spotify software and to stop using",
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
                # Spotify ToS: moral rights waiver
                "waive, and not to enforce, any moral rights",
                "waive and not to enforce any moral rights",
                "right to be identified as the author",
                "right to object to derogatory treatment",
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
                # Spotify: explicit ML/AI development from user data
                # LinkedIn: license survives deletion in several circumstances (linkedin_tos_004)
                "we had already sublicensed others prior to your content removal",
                "sublicensed others prior to your content removal or closing of your account",
                "for the reasonable time it takes to remove the content you delete from backup", # annotator: this is profiling/personalisation
                # not a content license. Kept in tracking_profiling MEDIUM instead.
                "development and training of algorithmic",
                "build ai features",
                # Google: AI-generated content cannot develop competing ML models (google_tos)
                "using ai-generated content from our services to develop machine learning models",
                "ai-generated content from our services to develop machine learning models or related ai technology",
                # Amazon: prohibition on using AI output to train competing models
                "use ai-generated content from the amazon services to, directly or indirectly, develop",
                "develop or improve large language or multimodal models",
                # Microsoft: broad content license to use/transmit/display content (ms_002 HIGH)
                "to make copies of, retain, transmit, reformat, display, and distribute via communication tools",
                "distribute via communication tools your content on the services",
                "your content may appear in demonstrations or materials that promote the service",
                # Microsoft: AI services data cannot be used to train any AI (microsoft_tos)
                "data from the ai services, to create, train, or improve",
                "create, train, or improve directly or indirectly any ai technology",
                "you may not use the ai services, or data from the ai services, to create",
                "improve our personalised recommendation algorithms",
                # Apple: Applebot web crawler as AI training source
                "apple uses applebot, a web crawler, to crawl information that is publicly available",
                "as a source for our foundational ai models",
                "train ai models",
                "train machine learning",
                "use your content to train",
                "use for machine learning",
                "use content for research and development",
                "use to improve our ai",
                # Discord: using public content to build automated moderation models
                "create systems and models that can be automated",
                "use content posted in larger spaces to help us develop",
                "use content posted in public spaces",
                "widely available on the service to create systems and models",
                "use that content to help us develop, improve, and power",
                # Meta-style AI training language
                "develop and improve ai for",
                "used to develop and improve ai",
                "may be used to develop and improve ai",
                "interactions with ai at meta and related metadata",
                "improve ai for meta products and for third parties",
            ],
            "MEDIUM": [
                # Standard content license (necessary but still worth flagging)
                "grant us a license",
                "you grant a license",
                "license to use your content",
                "worldwide license",
                "non-exclusive license",
                "royalty-free license",
                # Spotify ToS: feedback used without restriction or payment (spotify_tos_005)
                "feedback is not confidential and may be used by spotify without restriction and without payment",
                # Microsoft: feedback used commercially, create derivatives, no obligation (ms_003)
                "right to make, have made, create derivative works, use, share and commercialize your feedback in any way",
                "commercialize your feedback in any way and for any purpose",
                "may be used without restriction and without payment",
                "used without restriction and without payment to you",
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
