"""SMS verification code service.

For demo purposes, uses an in-memory store. In production, this would use Redis
and integrate with Aliyun SMS API.
"""

import random
import time

from app.core.config import settings

# In-memory store: phone -> (code, expiry_timestamp)
# In production, replace with Redis: SET phone code EX 300
_code_store: dict[str, tuple[str, float]] = {}

# Code validity in seconds
CODE_TTL = 300  # 5 minutes


def generate_verification_code(phone: str) -> str:
    """Generate and store a 6-digit verification code for the given phone.

    In demo/debug mode, always generates '123456' and prints to console.

    Args:
        phone: The mobile phone number.

    Returns:
        The generated code string.
    """
    if settings.DEBUG:
        # Demo mode: use fixed code
        code = "123456"
    else:
        code = f"{random.randint(0, 999999):06d}"

    _code_store[phone] = (code, time.time() + CODE_TTL)

    # Log the code for demo purposes
    print(f"[SMS] Verification code for {phone}: {code}")

    # In production, send via Aliyun SMS API:
    # send_sms(phone, code, settings.SMS_SIGN_NAME, settings.SMS_TEMPLATE_CODE)

    return code


def verify_code(phone: str, code: str) -> bool:
    """Verify a submitted code against the stored code.

    In demo/debug mode, the code '123456' is always accepted.

    Args:
        phone: The mobile phone number.
        code: The code submitted by the user.

    Returns:
        True if valid, False otherwise.
    """
    # Demo mode: accept '123456' for any phone number
    if settings.DEBUG and code == "123456":
        # Clean up any stored code
        _code_store.pop(phone, None)
        return True

    stored = _code_store.get(phone)
    if stored is None:
        return False

    stored_code, expiry = stored
    if time.time() > expiry:
        # Expired
        del _code_store[phone]
        return False

    if stored_code != code:
        return False

    # Code used successfully, remove it
    del _code_store[phone]
    return True
