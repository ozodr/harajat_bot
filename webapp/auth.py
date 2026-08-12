"""
🔐 Telegram WebApp initData tekshiruvi

Telegram hujjatiga muvofiq:
  secret_key = HMAC_SHA256(key="WebAppData", msg=bot_token)
  hash       = HMAC_SHA256(key=secret_key, msg=data_check_string)
"""
import hashlib
import hmac
import json
import logging
import time
from urllib.parse import parse_qsl

logger = logging.getLogger(__name__)

# initData shu muddatdan eski bo'lsa qabul qilinmaydi (24 soat)
MAX_AGE_SECONDS = 24 * 60 * 60


def _secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()


def validate_init_data(init_data: str, bot_token: str) -> dict | None:
    """initData'ni tekshirib, foydalanuvchi ma'lumotini qaytaradi. Xato bo'lsa None."""
    if not init_data:
        return None

    try:
        pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        return None

    data = dict(pairs)
    received_hash = data.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={data[k]}" for k in sorted(data))
    expected_hash = hmac.new(
        _secret_key(bot_token), data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        return None

    auth_date = data.get("auth_date")
    if not auth_date or not auth_date.isdigit():
        return None
    if time.time() - int(auth_date) > MAX_AGE_SECONDS:
        logger.info("initData muddati o'tgan")
        return None

    try:
        user = json.loads(data.get("user", "null"))
    except json.JSONDecodeError:
        return None

    if not isinstance(user, dict) or not isinstance(user.get("id"), int):
        return None

    return user
