"""
backend/notifications.py
Notification & Alert Hooks for Roomee Platform.
Supports structured logging, webhook triggers, and simulated email/SMS alerts.
"""
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger("roomee.notifications")
logging.basicConfig(level=logging.INFO)

def send_booking_notification(booking, event_type="created"):
    """
    Triggers student and property owner notification when a booking or visit is initiated or updated.
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    msg = {
        "event": f"booking_{event_type}",
        "timestamp": timestamp,
        "booking_id": booking.id,
        "booking_type": booking.booking_type,
        "status": booking.status,
        "user": {
            "id": booking.user_id,
            "name": booking.user.name if booking.user else "Student",
            "phone": booking.user.phone if booking.user else "",
            "email": booking.user.email if booking.user else ""
        },
        "property": {
            "id": booking.pg_id,
            "name": booking.property.name if booking.property else "Roomee Stay",
            "locality": booking.property.locality if booking.property else "",
            "city": booking.property.city if booking.property else ""
        },
        "details": {
            "room_type": booking.room.room_type if booking.room else "N/A",
            "move_in_date": booking.move_in_date,
            "visit_date": booking.visit_date,
            "visit_slot": booking.visit_slot,
            "token_amount": booking.token_amount
        }
    }

    # 1. Console structured alert
    logger.info(f"🔔 [NOTIFICATION - {event_type.upper()}] Booking #{booking.id}: {json.dumps(msg, indent=2)}")

    # 2. Webhook dispatch if configured via environment variable
    webhook_url = os.getenv("BOOKING_WEBHOOK_URL")
    if webhook_url:
        try:
            import urllib.request
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(msg).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(req, timeout=3)
        except Exception as e:
            logger.warning(f"Webhook dispatch error: {e}")

    return msg


def send_status_update_notification(booking, old_status, new_status):
    """
    Triggers alert when owner accepts or rejects a student's booking or visit.
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    msg = {
        "event": "booking_status_updated",
        "timestamp": timestamp,
        "booking_id": booking.id,
        "old_status": old_status,
        "new_status": new_status,
        "student_name": booking.user.name if booking.user else "Student",
        "student_phone": booking.user.phone if booking.user else "",
        "student_email": booking.user.email if booking.user else "",
        "property_name": booking.property.name if booking.property else "Roomee Stay"
    }
    logger.info(f"📣 [STATUS UPDATE] Booking #{booking.id} transitioned from '{old_status}' to '{new_status}' for student '{msg['student_name']}' at '{msg['property_name']}'.")
    return msg


def send_payment_notification(payment, booking):
    """
    Triggers payment confirmation receipt and alert to student and owner.
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    msg = {
        "event": "payment_confirmed",
        "timestamp": timestamp,
        "transaction_id": payment.transaction_id,
        "amount": payment.amount,
        "gateway": payment.payment_gateway,
        "booking_id": booking.id,
        "student_name": booking.user.name if booking.user else "Student",
        "student_phone": booking.user.phone if booking.user else "",
        "property_name": booking.property.name if booking.property else "Roomee Stay"
    }
    logger.info(f"💳 [PAYMENT SUCCESS] Received ₹{payment.amount} (Txn: {payment.transaction_id}) for Booking #{booking.id} via {payment.payment_gateway}.")
    return msg
