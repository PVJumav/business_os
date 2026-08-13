import os
import smtplib
from email.message import EmailMessage
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field


router = APIRouter(prefix="/public", tags=["Public Website"])

MAILBOXES = {
    "general": "contact@lunexao.com",
    "info": "info@lunexao.com",
    "careers": "careers@lunexao.com",
    "training": "training@lunexao.com",
    "webinars": "webinars@lunexao.com",
    "support": "support@lunexao.com",
}


class PublicContactPayload(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    company: Optional[str] = Field(default=None, max_length=160)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=80)
    interest: Optional[str] = Field(default=None, max_length=100)
    subject: Optional[str] = Field(default=None, max_length=160)
    message: str = Field(..., min_length=10, max_length=5000)
    form_type: Optional[str] = Field(default=None, max_length=80)
    role: Optional[str] = Field(default=None, max_length=160)
    location: Optional[str] = Field(default=None, max_length=160)
    availability: Optional[str] = Field(default=None, max_length=160)
    profile_link: Optional[str] = Field(default=None, max_length=500)
    website: Optional[str] = Field(default=None, max_length=200)


def _route_for(payload: PublicContactPayload) -> tuple[str, str]:
    text = " ".join(
        value or ""
        for value in [payload.interest, payload.subject, payload.form_type, payload.role]
    ).lower()
    if any(token in text for token in ["career", "job", "apply"]):
        return "Careers", MAILBOXES["careers"]
    if any(token in text for token in ["training", "academy", "course"]):
        return "Training", MAILBOXES["training"]
    if any(token in text for token in ["webinar", "event"]):
        return "Webinars", MAILBOXES["webinars"]
    if any(token in text for token in ["support", "customer success"]):
        return "Support", MAILBOXES["support"]
    if any(token in text for token in ["partnership", "media"]):
        return "Info", MAILBOXES["info"]
    return "General Enquiry", MAILBOXES["general"]


def _smtp_settings() -> dict[str, str | int | bool]:
    user = os.getenv("ZOHO_SMTP_USER") or os.getenv("SMTP_USER")
    password = os.getenv("ZOHO_SMTP_PASSWORD") or os.getenv("SMTP_PASSWORD")
    if not user or not password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Zoho email delivery is not configured.",
        )
    port = int(os.getenv("ZOHO_SMTP_PORT") or os.getenv("SMTP_PORT") or "465")
    return {
        "host": os.getenv("ZOHO_SMTP_HOST") or os.getenv("SMTP_HOST") or "smtp.zoho.com",
        "port": port,
        "user": user,
        "password": password,
        "from_email": os.getenv("CONTACT_FROM_EMAIL") or user,
        "use_ssl": os.getenv("ZOHO_SMTP_USE_SSL", "true").lower() != "false",
    }


def _message_text(payload: PublicContactPayload, route_label: str, to_email: str) -> str:
    lines = [
        f"Name: {payload.name}",
        f"Company: {payload.company or 'Not provided'}",
        f"Email: {payload.email}",
        f"Phone: {payload.phone or 'Not provided'}",
        f"Interest: {payload.interest or 'Not provided'}",
        f"Route: {route_label} <{to_email}>",
    ]
    if payload.role:
        lines.append(f"Role Applied For: {payload.role}")
    if payload.location:
        lines.append(f"Location: {payload.location}")
    if payload.availability:
        lines.append(f"Availability: {payload.availability}")
    if payload.profile_link:
        lines.append(f"Profile/CV Link: {payload.profile_link}")
    lines.extend(["", "Message:", payload.message])
    return "\n".join(lines)


def _send_zoho(payload: PublicContactPayload) -> tuple[str, str]:
    route_label, to_email = _route_for(payload)
    settings = _smtp_settings()
    subject_text = payload.subject or payload.role or payload.interest or "Website enquiry"
    message = EmailMessage()
    message["From"] = str(settings["from_email"])
    message["To"] = to_email
    message["Reply-To"] = str(payload.email)
    message["Subject"] = f"[{route_label}] {subject_text}"
    message.set_content(_message_text(payload, route_label, to_email))

    if settings["use_ssl"]:
        with smtplib.SMTP_SSL(str(settings["host"]), int(settings["port"]), timeout=20) as smtp:
            smtp.login(str(settings["user"]), str(settings["password"]))
            smtp.send_message(message)
    else:
        with smtplib.SMTP(str(settings["host"]), int(settings["port"]), timeout=20) as smtp:
            smtp.starttls()
            smtp.login(str(settings["user"]), str(settings["password"]))
            smtp.send_message(message)
    return route_label, to_email


@router.post("/contact")
def submit_public_contact(payload: PublicContactPayload):
    if payload.website:
        return {"ok": True, "routed_to": "bot-filter"}
    try:
        route_label, to_email = _send_zoho(payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Zoho email delivery failed. Check SMTP credentials and mailbox permissions.",
        ) from exc
    return {"ok": True, "department": route_label, "routed_to": to_email}
