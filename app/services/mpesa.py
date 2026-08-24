"""
Safaricom Daraja M-Pesa integration.

Covers the two flows the wallet needs:
  * STK Push ("Lipa na M-Pesa Online") for deposits — we prompt the
    player's phone, they enter their PIN, Safaricom posts a callback here.
  * B2C ("Business to Customer") for withdrawals — we push money out to
    the player's phone, Safaricom posts a result callback here.

All of this talks to the real Daraja API. Nothing here is a simulation —
point MPESA_ENV at "sandbox" while testing against Safaricom's sandbox
credentials, and at "production" once your go-live credentials and
security credential are issued.

Required environment variables (see config.py):
  MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET   — app credentials (OAuth)
  MPESA_SHORTCODE, MPESA_PASSKEY              — STK Push (paybill/till + passkey)
  MPESA_CALLBACK_URL                          — STK Push result webhook (public HTTPS URL)
  MPESA_ENV                                   — "sandbox" | "production"

  MPESA_INITIATOR_NAME                        — B2C API operator username
  MPESA_SECURITY_CREDENTIAL                   — initiator password encrypted with
                                                 Safaricom's public cert (base64) —
                                                 generate this offline, never the raw password
  MPESA_B2C_SHORTCODE                         — org shortcode enabled for B2C
  MPESA_B2C_RESULT_URL, MPESA_B2C_TIMEOUT_URL — B2C webhooks (public HTTPS URLs)
"""
import base64
import logging
import time
from datetime import datetime

import requests
from flask import current_app

logger = logging.getLogger(__name__)

_token_cache = {"access_token": None, "expires_at": 0}


class MpesaError(Exception):
    """Raised when Daraja rejects a request or is unreachable."""


def _base_url():
    env = current_app.config.get("MPESA_ENV", "sandbox")
    if env == "production":
        return "https://api.safaricom.co.ke"
    return "https://sandbox.safaricom.co.ke"


def get_access_token():
    """OAuth token, cached until ~60s before it expires."""
    now = time.time()
    if _token_cache["access_token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    consumer_key = current_app.config["MPESA_CONSUMER_KEY"]
    consumer_secret = current_app.config["MPESA_CONSUMER_SECRET"]
    if not consumer_key or not consumer_secret:
        raise MpesaError("MPESA_CONSUMER_KEY / MPESA_CONSUMER_SECRET are not configured")

    url = f"{_base_url()}/oauth/v1/generate?grant_type=client_credentials"
    resp = requests.get(url, auth=(consumer_key, consumer_secret), timeout=15)
    if resp.status_code != 200:
        logger.error("Daraja OAuth failed: %s %s", resp.status_code, resp.text)
        raise MpesaError(f"OAuth token request failed ({resp.status_code})")

    data = resp.json()
    token = data["access_token"]
    expires_in = int(data.get("expires_in", 3599))
    _token_cache["access_token"] = token
    _token_cache["expires_at"] = now + expires_in
    return token


def _normalize_msisdn(phone):
    """Accepts 07xxxxxxxx, +2547xxxxxxxx, or 2547xxxxxxxx -> returns 2547xxxxxxxx."""
    phone = "".join(ch for ch in str(phone) if ch.isdigit())
    if phone.startswith("0") and len(phone) == 10:
        return "254" + phone[1:]
    if phone.startswith("254") and len(phone) == 12:
        return phone
    if phone.startswith("7") and len(phone) == 9:
        return "254" + phone
    raise MpesaError(f"Unrecognized phone number format: {phone!r}")


def stk_push(phone_number, amount, account_reference, transaction_desc="Wallet deposit"):
    """Initiate an STK Push (Lipa na M-Pesa Online) prompt on the player's phone.

    Returns the Daraja response dict on success, containing
    CheckoutRequestID / MerchantRequestID that the caller must persist
    against a pending Transaction row so the callback can be matched up.
    """
    cfg = current_app.config
    shortcode = cfg["MPESA_SHORTCODE"]
    passkey = cfg["MPESA_PASSKEY"]
    callback_url = cfg["MPESA_CALLBACK_URL"]
    if not (shortcode and passkey and callback_url):
        raise MpesaError("MPESA_SHORTCODE / MPESA_PASSKEY / MPESA_CALLBACK_URL are not configured")

    token = get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()
    msisdn = _normalize_msisdn(phone_number)

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": msisdn,
        "PartyB": shortcode,
        "PhoneNumber": msisdn,
        "CallBackURL": callback_url,
        "AccountReference": str(account_reference)[:12],
        "TransactionDesc": transaction_desc[:13],
    }

    url = f"{_base_url()}/mpesa/stkpush/v1/processrequest"
    resp = requests.post(
        url, json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=20
    )
    data = resp.json() if resp.content else {}
    if resp.status_code != 200 or str(data.get("ResponseCode")) != "0":
        logger.error("STK Push failed: %s %s", resp.status_code, data)
        raise MpesaError(data.get("errorMessage") or data.get("ResponseDescription") or "STK Push request failed")

    return data


def stk_push_query(checkout_request_id):
    """Poll Daraja for the outcome of a previously-initiated STK Push.

    Useful for the frontend to poll while waiting instead of only relying
    on the async callback, and to detect user-cancelled/timeout prompts.
    """
    cfg = current_app.config
    shortcode = cfg["MPESA_SHORTCODE"]
    passkey = cfg["MPESA_PASSKEY"]
    token = get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id,
    }
    url = f"{_base_url()}/mpesa/stkpushquery/v1/query"
    resp = requests.post(
        url, json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=20
    )
    return resp.json() if resp.content else {}


def b2c_payment(phone_number, amount, remarks, occasion="Withdrawal"):
    """Send money out to a player's phone (withdrawal) via B2C.

    Returns the Daraja acknowledgement dict containing ConversationID /
    OriginatorConversationID — persist these against the pending
    Transaction row; the actual success/failure lands later at
    MPESA_B2C_RESULT_URL.
    """
    cfg = current_app.config
    initiator = cfg.get("MPESA_INITIATOR_NAME")
    security_credential = cfg.get("MPESA_SECURITY_CREDENTIAL")
    shortcode = cfg.get("MPESA_B2C_SHORTCODE")
    result_url = cfg.get("MPESA_B2C_RESULT_URL")
    timeout_url = cfg.get("MPESA_B2C_TIMEOUT_URL")
    if not all([initiator, security_credential, shortcode, result_url, timeout_url]):
        raise MpesaError(
            "B2C is not fully configured: need MPESA_INITIATOR_NAME, "
            "MPESA_SECURITY_CREDENTIAL, MPESA_B2C_SHORTCODE, "
            "MPESA_B2C_RESULT_URL, MPESA_B2C_TIMEOUT_URL"
        )

    token = get_access_token()
    msisdn = _normalize_msisdn(phone_number)

    payload = {
        "InitiatorName": initiator,
        "SecurityCredential": security_credential,
        "CommandID": "BusinessPayment",
        "Amount": int(amount),
        "PartyA": shortcode,
        "PartyB": msisdn,
        "Remarks": remarks[:100],
        "QueueTimeOutURL": timeout_url,
        "ResultURL": result_url,
        "Occasion": occasion[:100],
    }

    url = f"{_base_url()}/mpesa/b2c/v1/paymentrequest"
    resp = requests.post(
        url, json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=20
    )
    data = resp.json() if resp.content else {}
    if resp.status_code != 200 or str(data.get("ResponseCode")) != "0":
        logger.error("B2C payment request failed: %s %s", resp.status_code, data)
        raise MpesaError(data.get("errorMessage") or data.get("ResponseDescription") or "B2C request failed")

    return data


def parse_stk_callback(payload):
    """Normalize Safaricom's STK callback body into a flat dict.

    Returns None if the payload doesn't look like a Daraja STK callback.
    """
    try:
        body = payload["Body"]["stkCallback"]
    except (KeyError, TypeError):
        return None

    result = {
        "merchant_request_id": body.get("MerchantRequestID"),
        "checkout_request_id": body.get("CheckoutRequestID"),
        "result_code": body.get("ResultCode"),
        "result_desc": body.get("ResultDesc"),
        "amount": None,
        "mpesa_receipt": None,
        "phone_number": None,
        "transaction_date": None,
    }

    items = (body.get("CallbackMetadata") or {}).get("Item", [])
    for item in items:
        name = item.get("Name")
        value = item.get("Value")
        if name == "Amount":
            result["amount"] = value
        elif name == "MpesaReceiptNumber":
            result["mpesa_receipt"] = value
        elif name == "PhoneNumber":
            result["phone_number"] = value
        elif name == "TransactionDate":
            result["transaction_date"] = value

    return result


def parse_b2c_result(payload):
    """Normalize Safaricom's B2C result callback body into a flat dict."""
    try:
        result = payload["Result"]
    except (KeyError, TypeError):
        return None

    parsed = {
        "conversation_id": result.get("ConversationID"),
        "originator_conversation_id": result.get("OriginatorConversationID"),
        "result_code": result.get("ResultCode"),
        "result_desc": result.get("ResultDesc"),
        "transaction_amount": None,
        "mpesa_receipt": None,
        "receiver_phone": None,
    }

    items = (result.get("ResultParameters") or {}).get("ResultParameter", [])
    for item in items:
        key = item.get("Key")
        value = item.get("Value")
        if key == "TransactionAmount":
            parsed["transaction_amount"] = value
        elif key == "TransactionReceipt":
            parsed["mpesa_receipt"] = value
        elif key == "ReceiverPartyPublicName":
            parsed["receiver_phone"] = value

    return parsed
