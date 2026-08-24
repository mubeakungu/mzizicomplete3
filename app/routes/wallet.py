import logging
import uuid
from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models.wallet import Transaction
from app.services import mpesa

logger = logging.getLogger(__name__)

wallet_bp = Blueprint("wallet", __name__)


@wallet_bp.route("/")
@login_required
def overview():
    transactions = (
        current_user.wallet.transactions.order_by(Transaction.created_at.desc()).limit(50).all()
    )
    return render_template("wallet/overview.html", wallet=current_user.wallet, transactions=transactions)


# ---------------------------------------------------------------------------
# Deposits — STK Push
# ---------------------------------------------------------------------------

@wallet_bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    if request.method == "POST":
        daily_limit = current_app.config["DEFAULT_DAILY_DEPOSIT_LIMIT"]
        try:
            amount = Decimal(request.form.get("amount", "0"))
        except InvalidOperation:
            return render_template("wallet/deposit.html", error="Enter a valid amount.")

        phone = (request.form.get("phone") or current_user.phone_number or "").strip()

        if amount <= 0:
            return render_template("wallet/deposit.html", error="Enter a valid amount.")
        if amount > daily_limit:
            return render_template(
                "wallet/deposit.html",
                error=f"Deposits are capped at KES {daily_limit:,} per day. "
                      f"Reach out to support to adjust your limit.",
            )
        if not phone:
            return render_template("wallet/deposit.html", error="Enter the M-Pesa number to pay from.")

        reference = uuid.uuid4().hex[:20]
        txn = Transaction(
            wallet_id=current_user.wallet.id,
            type="deposit",
            amount=amount,
            balance_after=current_user.wallet.balance,  # unchanged until confirmed
            reference=reference,
            status="pending",
            phone_number=phone,
        )
        db.session.add(txn)
        db.session.commit()

        try:
            resp = mpesa.stk_push(
                phone_number=phone,
                amount=amount,
                account_reference=f"MB{current_user.id}",
                transaction_desc="Mzizibet deposit",
            )
        except mpesa.MpesaError as e:
            txn.status = "failed"
            txn.result_desc = str(e)
            db.session.commit()
            logger.error("STK push failed for txn %s: %s", txn.reference, e)
            return render_template(
                "wallet/deposit.html",
                error="We couldn't reach M-Pesa right now. Please try again in a moment.",
            )

        txn.checkout_request_id = resp.get("CheckoutRequestID")
        txn.merchant_request_id = resp.get("MerchantRequestID")
        db.session.commit()

        return render_template(
            "wallet/deposit_pending.html",
            amount=amount,
            checkout_request_id=txn.checkout_request_id,
        )

    return render_template("wallet/deposit.html")


@wallet_bp.route("/deposit/status/<checkout_request_id>")
@login_required
def deposit_status(checkout_request_id):
    """Polled by the deposit-pending page while waiting for the callback."""
    txn = Transaction.query.filter_by(
        checkout_request_id=checkout_request_id, wallet_id=current_user.wallet.id
    ).first()
    if not txn:
        return jsonify({"status": "unknown"}), 404
    return jsonify({
        "status": txn.status,
        "amount": float(txn.amount),
        "mpesa_receipt": txn.mpesa_receipt,
        "message": txn.result_desc,
    })


@wallet_bp.route("/mpesa/callback", methods=["POST"])
def mpesa_callback():
    """Daraja hits this after an STK Push attempt (success, cancel, or timeout).

    We only ever trust this by matching CheckoutRequestID to a pending
    Transaction row we created ourselves — never by ResultCode alone, and
    never by a client-side claim that a payment went through.
    """
    payload = request.get_json(silent=True) or {}
    parsed = mpesa.parse_stk_callback(payload)

    if not parsed:
        logger.warning("Unrecognized STK callback payload: %s", payload)
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

    txn = Transaction.query.filter_by(checkout_request_id=parsed["checkout_request_id"]).first()
    if not txn:
        logger.warning("STK callback for unknown CheckoutRequestID: %s", parsed["checkout_request_id"])
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

    if txn.status != "pending":
        # Already processed (Safaricom can retry callbacks) — ack and stop.
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

    if parsed["result_code"] == 0:
        # Trust the amount Safaricom confirms, not what the client requested.
        confirmed_amount = Decimal(str(parsed["amount"])) if parsed["amount"] is not None else txn.amount

        wallet = txn.wallet
        wallet.balance = (wallet.balance or Decimal("0")) + confirmed_amount
        txn.amount = confirmed_amount
        txn.balance_after = wallet.balance
        txn.mpesa_receipt = parsed["mpesa_receipt"]
        txn.status = "completed"
        txn.result_desc = parsed["result_desc"]
    else:
        txn.status = "failed"
        txn.result_desc = parsed["result_desc"]

    db.session.commit()
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})


# ---------------------------------------------------------------------------
# Withdrawals — B2C
# ---------------------------------------------------------------------------

@wallet_bp.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    if request.method == "POST":
        try:
            amount = Decimal(request.form.get("amount", "0"))
        except InvalidOperation:
            return render_template("wallet/withdraw.html", error="Enter a valid amount.")

        min_w = current_app.config["MIN_WITHDRAWAL"]
        max_w = current_app.config["MAX_WITHDRAWAL_PER_TRANSACTION"]
        wallet = current_user.wallet

        if amount < min_w:
            return render_template("wallet/withdraw.html", error=f"Minimum withdrawal is KES {min_w}.")
        if amount > max_w:
            return render_template("wallet/withdraw.html", error=f"Maximum per withdrawal is KES {max_w:,}.")
        if amount > (wallet.balance or Decimal("0")):
            return render_template("wallet/withdraw.html", error="Insufficient balance.")

        # AML/KYC: withdrawals always go to the account's own verified phone number,
        # never to an arbitrary number entered in the form.
        phone = current_user.phone_number
        if not phone:
            return render_template("wallet/withdraw.html", error="No verified phone number on file.")

        reference = uuid.uuid4().hex[:20]

        # Hold the funds immediately so the same balance can't be withdrawn twice
        # while the B2C request is in flight; refunded automatically on failure.
        wallet.balance -= amount
        txn = Transaction(
            wallet_id=wallet.id,
            type="withdrawal",
            amount=amount,
            balance_after=wallet.balance,
            reference=reference,
            status="pending",
            phone_number=phone,
        )
        db.session.add(txn)
        db.session.commit()

        try:
            resp = mpesa.b2c_payment(
                phone_number=phone,
                amount=amount,
                remarks=f"Mzizibet withdrawal {reference}",
            )
        except mpesa.MpesaError as e:
            # Refund the hold — the request never reached Safaricom successfully.
            wallet.balance += amount
            txn.status = "failed"
            txn.result_desc = str(e)
            txn.balance_after = wallet.balance
            db.session.commit()
            logger.error("B2C request failed for txn %s: %s", txn.reference, e)
            return render_template(
                "wallet/withdraw.html",
                error="We couldn't reach M-Pesa right now. Your balance hasn't been touched.",
            )

        txn.conversation_id = resp.get("ConversationID")
        txn.originator_conversation_id = resp.get("OriginatorConversationID")
        db.session.commit()

        flash("Withdrawal requested — funds should land on your phone shortly.", "info")
        return redirect(url_for("wallet.overview"))

    return render_template("wallet/withdraw.html")


@wallet_bp.route("/mpesa/b2c/result", methods=["POST"])
def mpesa_b2c_result():
    """Daraja hits this once a B2C payout has actually been attempted."""
    payload = request.get_json(silent=True) or {}
    parsed = mpesa.parse_b2c_result(payload)

    if not parsed:
        logger.warning("Unrecognized B2C result payload: %s", payload)
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

    txn = Transaction.query.filter_by(conversation_id=parsed["conversation_id"]).first()
    if not txn or txn.status != "pending":
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

    if parsed["result_code"] == 0:
        txn.status = "completed"
        txn.mpesa_receipt = parsed["mpesa_receipt"]
        txn.result_desc = parsed["result_desc"]
    else:
        # Payout failed after we'd already held the funds — refund the wallet.
        wallet = txn.wallet
        wallet.balance = (wallet.balance or Decimal("0")) + txn.amount
        txn.balance_after = wallet.balance
        txn.status = "failed"
        txn.result_desc = parsed["result_desc"]

    db.session.commit()
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})


@wallet_bp.route("/mpesa/b2c/timeout", methods=["POST"])
def mpesa_b2c_timeout():
    """Daraja hits this if the B2C request itself timed out (not the same as a
    completed-but-failed payout, which arrives at /mpesa/b2c/result)."""
    payload = request.get_json(silent=True) or {}
    parsed = mpesa.parse_b2c_result(payload) or {}
    conversation_id = parsed.get("conversation_id")

    txn = Transaction.query.filter_by(conversation_id=conversation_id).first() if conversation_id else None
    if txn and txn.status == "pending":
        wallet = txn.wallet
        wallet.balance = (wallet.balance or Decimal("0")) + txn.amount
        txn.balance_after = wallet.balance
        txn.status = "failed"
        txn.result_desc = "Request timed out"
        db.session.commit()

    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})
