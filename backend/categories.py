"""
categories.py — ClauseGuard Risk Category Definitions

Each category has:
  - label:       Human-readable name
  - description: Short explanation
  - weight:      Contribution to overall risk score (all weights sum to 1.0)
  - rules:       Keyword lists per risk level (HIGH / MEDIUM / LOW)

Design principle:
  HIGH   = direct, explicit harm to user data rights
  MEDIUM = concerning but common industry practice
  LOW    = present but relatively standard / disclosed language
"""

CATEGORIES: dict = {

    "data_sharing": {
        "label": "Data Sharing",
        "description": "Clauses authorizing sharing of user data with third parties",
        "weight": 0.25,
        "rules": {
            "HIGH": [
                "sell your data",
                "sell your information",
                "sell personal data",
                "sell user data",
                "sell to third parties",
                "share with advertisers",
                "monetize your data",
                "data broker",
                "sold to partners",
            ],
            "MEDIUM": [
                "share with third parties",
                "share with our partners",
                "share with affiliates",
                "share your information",
                "share personal data",
                "disclose to third parties",
                "disclose personal information",
                "transfer to third parties",
                "transfer your data",
                "disclosed to partners",
            ],
            "LOW": [
                "share with service providers",
                "share with vendors",
                "share aggregated data",
                "share anonymized data",
                "share non-personal information",
                "share de-identified",
            ],
        },
    },

    "tracking_profiling": {
        "label": "Tracking & Profiling",
        "description": "Clauses enabling behavioral tracking or user profiling",
        "weight": 0.20,
        "rules": {
            "HIGH": [
                "behavioral profiling",
                "cross-site tracking",
                "track across websites",
                "track across apps",
                "build a profile",
                "infer sensitive attributes",
                "device fingerprinting",
                "fingerprint your device",
                "persistent identifier",
                "track your activity across",
            ],
            "MEDIUM": [
                "track your usage",
                "track your activity",
                "personalized advertising",
                "targeted advertising",
                "behavioral advertising",
                "interest-based advertising",
                "advertising partners",
                "analytics partners",
                "web beacons",
                "pixel tags",
                "track clicks",
                "track purchases",
            ],
            "LOW": [
                "use cookies",
                "analytics",
                "log files",
                "session data",
                "usage data",
                "improve our services",
                "remember your preferences",
            ],
        },
    },

    "third_party_access": {
        "label": "Third-Party Access",
        "description": "Clauses granting third parties access to user data or accounts",
        "weight": 0.15,
        "rules": {
            "HIGH": [
                "grant third parties access",
                "third parties may access your",
                "allow third parties to collect",
                "third-party access to your account",
                "government access",
                "law enforcement access without notice",
                "national security",
                "intelligence agencies",
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
            ],
            "LOW": [
                "third-party links",
                "external websites",
                "third-party content",
                "linked services",
            ],
        },
    },

    "data_retention": {
        "label": "Data Retention",
        "description": "Clauses specifying how long user data is kept",
        "weight": 0.15,
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
            ],
            "MEDIUM": [
                "retain for as long as necessary",
                "retain after account closure",
                "backup copies may persist",
                "retain for business purposes",
                "may retain your data",
                "retain for an extended period",
                "stored even after deletion",
            ],
            "LOW": [
                "retain as required by law",
                "retain for legal obligations",
                "retain for a limited period",
                "deleted upon request",
                "retention policy",
            ],
        },
    },

    "arbitration": {
        "label": "Arbitration & Dispute Resolution",
        "description": "Clauses limiting user rights through mandatory arbitration",
        "weight": 0.15,
        "rules": {
            "HIGH": [
                "waive your right to a jury trial",
                "waive right to jury",
                "class action waiver",
                "waive right to class action",
                "binding arbitration",
                "you waive any right",
                "waive the right to participate in a class",
                "no class arbitration",
                "you give up your right",
            ],
            "MEDIUM": [
                "mandatory arbitration",
                "disputes resolved by arbitration",
                "arbitration agreement",
                "submit to arbitration",
                "resolve disputes through arbitration",
                "arbitration shall be final",
            ],
            "LOW": [
                "alternative dispute resolution",
                "mediation",
                "governing law",
                "jurisdiction",
                "arbitration preferred",
            ],
        },
    },

    "liability_limitation": {
        "label": "Liability Limitation",
        "description": "Clauses limiting the company's legal liability to the user",
        "weight": 0.10,
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
            ],
            "MEDIUM": [
                "limit our liability",
                "not responsible for any loss",
                "provided as is",
                "provided as-is",
                "without warranty",
                "we do not warrant",
                "we make no representations",
                "no guarantees",
            ],
            "LOW": [
                "liability limited to fees paid",
                "to the extent permitted by law",
                "some jurisdictions do not allow",
                "limitation of liability",
            ],
        },
    },
}

# Numeric ordering for risk level comparison
RISK_LEVEL_ORDER: dict[str, int] = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

# Base score contribution for each risk level
RISK_LEVEL_SCORES: dict[str, int] = {"LOW": 25, "MEDIUM": 60, "HIGH": 100}
