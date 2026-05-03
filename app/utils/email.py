
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

async def send_order_confirmation(to_email: str, order) -> None:

    settings = get_settings()

    subject = f"Order Confirmed — {order.id}"
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

        logger.info(
            f"[Email - DEV MODE] Would send to {to_email}:\n"
            f"  Subject: {subject}\n"
            f"  Body:\n{body}"
        )

async def send_welcome_email(to_email: str, name: str) -> None:

    settings = get_settings()

    subject = "Welcome to DIY Gift Basket!"
    body = (
        f"Hi {name or 'there'},\n\n"
        f"Welcome to DIY Gift Basket! We are thrilled to have you.\n\n"
        f"You can now start building custom gift baskets for your loved ones.\n\n"
        f"Cheers,\n"
        f"The DIY Gift Basket Team\n"
    )

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
            logger.info(f"[Email] Welcome sent to {to_email}")

        except Exception as e:
            logger.error(f"[Email] Failed to send welcome to {to_email}: {e}")
    else:
        logger.info(
            f"[Email - DEV MODE] Would send welcome to {to_email}:\n"
            f"  Subject: {subject}\n"
            f"  Body:\n{body}"
        )
async def send_password_reset_email(to_email: str, token: str) -> None:

    settings = get_settings()

    reset_link = f"http://localhost:5173/reset-password?token={token}"

    subject = "Reset Your Password — DIY Gift Basket"
    body = (
        f"Hi there,\n\n"
        f"We received a request to reset your password for your DIY Gift Basket account.\n\n"
        f"Click the link below to set a new password:\n"
        f"{reset_link}\n\n"
        f"This link will expire in 15 minutes. If you didn't request this, you can safely ignore this email.\n\n"
        f"Cheers,\n"
        f"The DIY Gift Basket Team\n"
    )

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
            logger.info(f"[Email] Password reset sent to {to_email}")

        except Exception as e:
            logger.error(f"[Email] Failed to send reset to {to_email}: {e}")
    else:
        logger.info(
            f"[Email - DEV MODE] Would send password reset to {to_email}:\n"
            f"  Subject: {subject}\n"
            f"  Body:\n{body}"
        )