"""
Subscription Plan Credit Limits Configuration.
Defines hardcoded credit limits and features per subscription plan tier.
"""

from typing import Dict, Any

PLAN_CREDIT_LIMITS: Dict[str, Dict[str, Any]] = {
    "discover": {
        "generationcreditstotal": 50,
        "videocreditstotal": 10,
        "voicecreditstotal": 20,
        "voiceclonecreditstotal": 5,
        "ugccreditstotal": 10,
        "imagecreditstotal": 50,
        "imagetovideocreditstotal": 10,
        "analysiscreditsunlimited": False,
    },
    "all access 99": {
        "generationcreditstotal": 500,
        "videocreditstotal": 100,
        "voicecreditstotal": 200,
        "voiceclonecreditstotal": 50,
        "ugccreditstotal": 100,
        "imagecreditstotal": 500,
        "imagetovideocreditstotal": 100,
        "analysiscreditsunlimited": False,
    },
    "all access 99 yearly": {
        "generationcreditstotal": 6000,
        "videocreditstotal": 1200,
        "voicecreditstotal": 2400,
        "voiceclonecreditstotal": 600,
        "ugccreditstotal": 1200,
        "imagecreditstotal": 6000,
        "imagetovideocreditstotal": 1200,
        "analysiscreditsunlimited": True,
    },
    "quickads_tier4": {
        "generationcreditstotal": 1000,
        "videocreditstotal": 250,
        "voicecreditstotal": 500,
        "voiceclonecreditstotal": 100,
        "ugccreditstotal": 250,
        "imagecreditstotal": 1000,
        "imagetovideocreditstotal": 250,
        "analysiscreditsunlimited": False,
    },
    "quickads_tier6": {
        "generationcreditstotal": 2500,
        "videocreditstotal": 600,
        "voicecreditstotal": 1200,
        "voiceclonecreditstotal": 250,
        "ugccreditstotal": 600,
        "imagecreditstotal": 2500,
        "imagetovideocreditstotal": 600,
        "analysiscreditsunlimited": True,
    },
    "enterprise": {
        "generationcreditstotal": 99999,
        "videocreditstotal": 99999,
        "voicecreditstotal": 99999,
        "voiceclonecreditstotal": 99999,
        "ugccreditstotal": 99999,
        "imagecreditstotal": 99999,
        "imagetovideocreditstotal": 99999,
        "analysiscreditsunlimited": True,
    },
}


def get_plan_credit_limits(plan_name: str) -> Dict[str, Any]:
    """
    Retrieve credit limits for a given subscription plan name.
    Normalizes inputs (case-insensitive, trimmed).
    Defaults to 'discover' plan if plan_name is not recognized.
    """
    if not plan_name:
        return PLAN_CREDIT_LIMITS["discover"].copy()

    normalized_key = str(plan_name).strip().lower()
    if normalized_key in PLAN_CREDIT_LIMITS:
        return PLAN_CREDIT_LIMITS[normalized_key].copy()

    # Check for alias matches (e.g. spaces or underscores)
    cleaned_key = normalized_key.replace("_", " ")
    if cleaned_key in PLAN_CREDIT_LIMITS:
        return PLAN_CREDIT_LIMITS[cleaned_key].copy()

    return PLAN_CREDIT_LIMITS["discover"].copy()
