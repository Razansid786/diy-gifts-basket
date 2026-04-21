"""
app/utils/email.py
──────────────────
Email sending utility (FR26 — order confirmation).

In development mode (no SMTP creds configured), emails are logged
to the console instead of sent.  Plug in real SMTP credentials
in ``.env`` for production use.
"""

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def send_order_confirmation(to_email: str, order) -> None:
    """
    Send an order confirmation email to the customer (FR26).

    Parameters
    ----------
    to_email : str
        Recipient email address.
    order : Order
        The order ORM object (used to build the email body).

    Notes
    -----
    If SMTP credentials are not configured, the email content is
    logged to stdout for development purposes.
    """
    settings = get_settings()

    subject = f"Order Confirmed — #{order.id[:8].upper()}"
    body = (
        f"Hi there!\n\n"
        f"Your order has been placed successfully.\n\n"
        f"Order ID   : {order.id}\n"
        f"Status     : {order.status}\n"
        f"Subtotal   : ${order.subtotal}\n"
        f"Shipping   : ${order.shipping_fee}\n"
        f"Total      : ${order.total}\n"
        f"Payment Ref: {order.payment_ref}\n\n"
        f"Thank you for shopping with DIY Gift Basket!\n"
    )

    # Check if SMTP is configured
    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

            mail_config = ConnectionConfig(
                MAIL_USERNAME=settings.SMTP_USER,
                MAIL_PASSWORD=settings.SMTP_PASSWORD,
                MAIL_FROM=settings.MAIL_FROM,
                MAIL_PORT=settings.SMTP_PORT,
                MAIL_SERVER=settings.SMTP_HOST,
                MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
                MAIL_STARTTLS=True,
                MAIL_SSL_TLS=False,
                USE_CREDENTIALS=True,
            )

            message = MessageSchema(
                subject=subject,
                recipients=[to_email],
                body=body,
                subtype=MessageType.plain,
            )

            fm = FastMail(mail_config)
            await fm.send_message(message)
            logger.info(f"[Email] Confirmation sent to {to_email}")

        except Exception as e:
            logger.error(f"[Email] Failed to send to {to_email}: {e}")
    else:
        # Development fallback — log to console
        logger.info(
            f"[Email - DEV MODE] Would send to {to_email}:\n"
            f"  Subject: {subject}\n"
            f"  Body:\n{body}"
        )
