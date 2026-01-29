"""SMTP delivery."""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def send_email(
    subject: str,
    sender_name: str,
    sender_address: str,
    to_addresses: list[str],
    html_body: str,
    text_body: str,
    smtp_host: str,
    smtp_port: int,
    use_tls: bool,
) -> None:
    password = os.getenv("SMTP_PASSWORD")
    if not password:
        raise RuntimeError("SMTP_PASSWORD env var is required")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender_address}>"
    msg["To"] = ", ".join(to_addresses)
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    if use_tls:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(sender_address, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(sender_address, password)
            server.send_message(msg)
