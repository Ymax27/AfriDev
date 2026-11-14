#!/usr/bin/env python3
"""Deterministic demo dataset for AfriDev Hub.

Usage:
    python scripts/seed_demo.py
    python scripts/seed_demo.py --reset

Every generated record is flagged ``is_demo``. ``--reset`` removes demo records
only; real accounts, projects and reputation ledgers are never deleted.
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, func, select  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.core.enums import (  # noqa: E402
    CollaborationMode,
    ContributionDomain,
    MissionStatus,
)
from app.modules.api_directory.models import APIEntry  # noqa: E402
from app.modules.contributions import service as contribution_service  # noqa: E402
from app.modules.contributions.models import ContributionRequest  # noqa: E402
from app.modules.contributions.schemas import ContributionCreate  # noqa: E402
from app.modules.countries.models import Country  # noqa: E402
from app.modules.field_reports import service as field_report_service  # noqa: E402
from app.modules.field_reports.models import FieldReport  # noqa: E402
from app.modules.knowledge import service as knowledge_service  # noqa: E402
from app.modules.knowledge.models import KnowledgeProblem, Solution  # noqa: E402
from app.modules.knowledge.schemas import ProblemCreate, SolutionCreate  # noqa: E402
from app.modules.messaging.models import (  # noqa: E402
    Conversation,
    ConversationMember,
    Message,
)
from app.modules.missions.models import Mission, MissionSubmission  # noqa: E402
from app.modules.projects import service as project_service  # noqa: E402
from app.modules.projects.models import (  # noqa: E402
    Project,
    ProjectFeedback,
    ProjectLike,
    ProjectPass,
)
from app.modules.projects.schemas import ProjectCreate  # noqa: E402
from app.modules.reputation import service as reputation_service  # noqa: E402
from app.modules.reputation.models import ReputationTransaction  # noqa: E402
from app.modules.users.models import User, UserRole, UserSkill  # noqa: E402

RNG = random.Random(2026)
SEED_LABEL = "DEMO"

COUNTRIES = [
    ("CM", "Cameroon", "Cameroun", "🇨🇲"),
    ("NG", "Nigeria", "Nigéria", "🇳🇬"),
    ("KE", "Kenya", "Kenya", "🇰🇪"),
    ("GH", "Ghana", "Ghana", "🇬🇭"),
    ("SN", "Senegal", "Sénégal", "🇸🇳"),
    ("CI", "Côte d'Ivoire", "Côte d'Ivoire", "🇨🇮"),
    ("ZA", "South Africa", "Afrique du Sud", "🇿🇦"),
    ("RW", "Rwanda", "Rwanda", "🇷🇼"),
]

FIRST_NAMES = [
    "Amina", "Chidi", "Fatou", "Kwame", "Lerato", "Moussa", "Ngozi", "Oluwaseun",
    "Awa", "Tunde", "Zainab", "Kofi", "Naledi", "Ibrahim", "Thandi", "Emeka",
    "Aicha", "Sipho", "Youssef", "Mariam", "Kelechi", "Aline", "Hassan", "Bintou",
]
LAST_NAMES = [
    "Nkeng", "Okafor", "Diop", "Mensah", "Mokoena", "Traoré", "Adeyemi", "Boakye",
    "Kouassi", "Nkemdirim", "Diallo", "Osei", "Dlamini", "Bello", "Ndlovu", "Eze",
    "Sow", "Mahlangu", "Camara", "Abebe", "Onyeka", "Mukamana", "Yao", "Touré",
]
SKILLS = ["TypeScript", "Python", "React", "FastAPI", "PostgreSQL", "Flutter", "Go", "Rust", "Docker", "React Native"]
CITIES = {
    "CM": ["Douala", "Yaoundé", "Bafoussam"],
    "NG": ["Lagos", "Abuja", "Kano"],
    "KE": ["Nairobi", "Mombasa", "Kisumu"],
    "GH": ["Accra", "Kumasi", "Tamale"],
    "SN": ["Dakar", "Thiès", "Saint-Louis"],
    "CI": ["Abidjan", "Bouaké", "Yamoussoukro"],
    "ZA": ["Cape Town", "Johannesburg", "Durban"],
    "RW": ["Kigali", "Butare", "Musanze"],
}

TECH_STACKS = [
    ["React", "TypeScript", "Tailwind CSS"],
    ["Python", "FastAPI", "PostgreSQL"],
    ["Flutter", "Dart", "Firebase"],
    ["Node.js", "Express", "MongoDB"],
    ["Go", "PostgreSQL", "Docker"],
    ["React Native", "TypeScript", "Expo"],
    ["Vue.js", "TypeScript", "Supabase"],
    ["Rust", "Actix", "PostgreSQL"],
]
CATEGORIES = ["web", "mobile", "fintech", "agritech", "healthtech", "edtech", "devtools", "civictech"]
PROJECT_NAMES = [
    "SawaPay", "KilimoTrack", "Mboa Health", "Nkwa Wallet", "Zuri Learn", "TerraFarm",
    "Kente Commerce", "Baobab Analytics", "Ubuntu LMS", "Sokoni Market", "Nala Ride",
    "Afya Connect", "Jua Power", "Mali Ledger", "Sankofa Archive", "Wazi Forms",
    "Tuma Delivery", "Kaya Build", "Farafina Pay", "Amara Clinic", "Dunia Maps",
    "Elimu Quiz", "Boda Fleet", "Mkulima Data", "Serengeti Cloud", "Kudi Savings",
    "Lumiere Studio", "Nyumbani Home", "Pula Weather", "Mazao Market", "Zeela Beauty",
    "Kobo Books", "Amani Support", "Wingu Storage", "Tamu Kitchen", "Moja Transit",
    "Baraka Micro", "Sifa Reviews", "Kazi Jobs", "Tena Repairs",
]

API_ENTRIES = [
    ("MTN Mobile Money API", "MTN Group", "payments", "Mobile money collections, disbursements and KYC via MTN MoMo.", "https://momodeveloper.mtn.com", "Sandbox free, production fees per transaction", ["CM", "GH", "CI", "RW", "NG", "ZA"]),
    ("Orange Money Web API", "Orange", "payments", "Orange Money payments and cash-in/cash-out for West and Central Africa.", "https://developer.orange.com", "Revenue share per transaction", ["CM", "CI", "SN"]),
    ("Wave Business API", "Wave Mobile Money", "payments", "Low-cost mobile money transfers and checkout for Senegal and Côte d'Ivoire.", "https://docs.wave.com", "1% withdrawal fee", ["SN", "CI"]),
    ("Flutterwave v4", "Flutterwave", "billing", "Cards, mobile money and bank transfers across 30+ African markets.", "https://developer.flutterwave.com", "1.4% local cards", ["NG", "GH", "KE", "ZA", "CM"]),
    ("Paystack API", "Paystack", "payments", "Card, bank and USSD payments with strong developer tooling.", "https://paystack.com/docs/api", "1.5% + fixed fee", ["NG", "GH", "ZA", "KE"]),
    ("Africa's Talking SMS", "Africa's Talking", "communication", "Bulk SMS, USSD and voice across African mobile networks.", "https://developers.africastalking.com", "Pay-as-you-go", ["KE", "NG", "GH", "CM", "SN", "RW", "ZA", "CI"]),
    ("Termii Messaging", "Termii", "communication", "Transactional SMS, WhatsApp and OTP delivery in Nigeria.", "https://developers.termii.com", "From NGN 2.50 per SMS", ["NG"]),
    ("Smile ID", "Smile Identity", "identity", "KYC, document verification and biometric checks for African IDs.", "https://docs.usesmileid.com", "Per-verification pricing", ["NG", "KE", "GH", "ZA", "RW"]),
    ("Google Maps Platform", "Google", "localization", "Geocoding, places and routing with African address coverage.", "https://developers.google.com/maps", "Monthly credit", ["CM", "NG", "KE", "GH", "SN", "CI", "ZA", "RW"]),
    ("Masakhane NLP Models", "Masakhane", "languages", "Open NLP models and datasets for African languages.", "https://github.com/masakhane-io", "Open source / free", ["ZA", "NG", "KE", "GH"]),
    ("pawaPay", "pawaPay", "payments", "Single mobile money API covering 20+ African operators and countries.", "https://docs.pawapay.io", "Per-transaction fee", ["NG", "GH", "KE", "CM", "SN", "CI", "RW", "ZA"]),
    ("Kkiapay", "Kkiapay", "payments", "Mobile money and card checkout for West African merchants.", "https://docs.kkiapay.me", "1.9% per transaction", ["SN", "CI", "CM", "BJ"]),
    ("Infobip SMS", "Infobip", "communication", "Global SMS, WhatsApp and email delivery with African routes.", "https://www.infobip.com/docs/api", "Per-message pricing", ["ZA", "NG", "KE", "GH", "CM"]),
    ("Beem Africa", "Beem", "communication", "SMS, USSD and airtime APIs widely used in East Africa.", "https://docs.beem.africa", "Pay-as-you-go", ["TZ", "KE", "UG", "RW"]),
    ("Dojah", "Dojah", "identity", "KYC, document checks and AML screening for African markets.", "https://docs.dojah.io", "Per-verification pricing", ["NG", "GH", "KE", "ZA"]),
    ("OkHi", "OkHi", "localization", "Address verification for African cities without reliable street addresses.", "https://docs.okhi.co", "Per-verification pricing", ["KE", "NG", "ZA"]),
    ("PayDunya", "PayDunya", "billing", "Recurring billing and payment links for francophone Africa.", "https://paydunya.com/developers", "2% per transaction", ["SN", "CI", "CM", "BJ", "TG"]),
    ("Lelapa AI InkubaLM", "Lelapa AI", "languages", "Small multilingual models for African languages and local use cases.", "https://lelapa.ai", "Commercial licence", ["ZA", "NG", "KE"]),
    ("Khaya AI Translation", "Khaya AI", "languages", "Translation and speech APIs for Ghanaian and West African languages.", "https://khaya.ai/docs", "Usage based", ["GH", "NG", "CI"]),
    # Payments
    ("M-Pesa Daraja API", "Safaricom", "payments", "STK push, C2B and B2C mobile money flows on Kenya's M-Pesa network.", "https://developer.safaricom.co.ke", "Paybill transaction fees", ["KE", "TZ", "GH"]),
    ("Airtel Money Collections", "Airtel Africa", "payments", "Collections and disbursements on the Airtel Money wallet across 14 markets.", "https://developers.airtel.africa", "Per-transaction fee", ["KE", "UG", "TZ", "RW", "NG", "ZM"]),
    ("Hubtel Payments", "Hubtel", "payments", "Mobile money, card and wallet checkout for Ghanaian merchants.", "https://developers.hubtel.com", "Negotiated per transaction", ["GH"]),
    ("Paymob Accept", "Paymob", "payments", "Card and wallet acceptance with installments for North African merchants.", "https://developers.paymob.com", "2.75% per transaction", ["EG", "KE", "OM", "SA"]),
    # Billing
    ("Yoco Online Payments", "Yoco", "billing", "Card checkout and payment links for South African small businesses.", "https://developer.yoco.com", "2.95% + fixed fee", ["ZA"]),
    ("Peach Payments", "Peach Payments", "billing", "Card, EFT and recurring billing rails across Southern Africa.", "https://developer.peachpayments.com", "Per-transaction fee", ["ZA", "KE", "MU"]),
    ("DPO Group Payment API", "Network International", "billing", "Single payment gateway covering 20+ African countries and currencies.", "https://docs.dpopay.com", "Negotiated per transaction", ["KE", "NG", "GH", "ZA", "TZ", "UG", "RW"]),
    ("SeerBit", "SeerBit", "billing", "Card, transfer and USSD checkout with subscriptions and split payments.", "https://doc.seerbit.com", "1.5% capped fee", ["NG", "GH", "KE"]),
    ("Fincra", "Fincra", "billing", "Collections, payouts and virtual accounts for African businesses.", "https://docs.fincra.com", "Per-transaction fee", ["NG", "GH", "KE", "ZA"]),
    ("Pesapal", "Pesapal", "billing", "Checkout and recurring billing used by East African merchants and schools.", "https://developer.pesapal.com", "Per-transaction fee", ["KE", "UG", "TZ"]),
    ("Cellulant Tingg", "Cellulant", "billing", "Pan-African collections and payouts with a single integration and settlement API.", "https://docs.tingg.africa", "Negotiated per transaction", ["KE", "NG", "GH", "TZ", "UG", "ZM", "RW"]),
    ("Interswitch Payment API", "Interswitch", "billing", "Card payments, transfers and bill payments for West African merchants.", "https://developer.interswitchgroup.com", "Negotiated per transaction", ["NG", "GH", "KE"]),
    # Communication
    ("Twilio Messaging", "Twilio", "communication", "Programmable SMS, WhatsApp and voice with African sender routes.", "https://www.twilio.com/docs/messaging", "Per-message pricing", ["ZA", "NG", "KE", "GH", "CM", "SN", "CI", "RW"]),
    ("WhatsApp Business Cloud API", "Meta", "communication", "Official WhatsApp messaging for notifications and support conversations.", "https://developers.facebook.com/docs/whatsapp/cloud-api", "Per-conversation pricing", ["NG", "KE", "ZA", "GH", "CM", "CI", "SN", "RW"]),
    ("Vonage Messages API", "Vonage", "communication", "SMS, WhatsApp and Viber delivery through one messages endpoint.", "https://developer.vonage.com/en/messages", "Per-message pricing", ["ZA", "NG", "KE", "GH"]),
    ("Sendchamp", "Sendchamp", "communication", "SMS, WhatsApp and email delivery with local Nigerian sender IDs.", "https://docs.sendchamp.com", "From NGN 2.40 per SMS", ["NG", "GH"]),
    ("360dialog WhatsApp API", "360dialog", "communication", "WhatsApp Business API hosting with per-message billing.", "https://docs.360dialog.com", "Per-message pricing", ["KE", "NG", "ZA", "GH"]),
    ("MailerSend", "MailerSend", "communication", "Transactional email with templates, domains and delivery webhooks.", "https://developers.mailersend.com", "Free tier then per email", ["ZA", "NG", "KE"]),
    # Identity
    ("VerifyMe Identity API", "VerifyMe", "identity", "NIN, BVN and document verification for Nigerian customers.", "https://docs.verifyme.ng", "Per-verification pricing", ["NG"]),
    ("IdentityPass", "Premise", "identity", "Identity, address and business verification across African markets.", "https://docs.identitypass.com", "Per-verification pricing", ["NG", "KE", "GH", "ZA", "UG"]),
    ("Youverify", "Youverify", "identity", "KYC, AML screening and liveness checks for regulated African businesses.", "https://docs.youverify.co", "Per-verification pricing", ["NG", "GH", "KE", "ZA", "CI"]),
    ("Seamfix ID Verification", "Seamfix", "identity", "Biometric capture and ID validation used by African telecoms and banks.", "https://seamfix.com/products", "Enterprise contract", ["NG", "GH", "KE", "ZA"]),
    ("QoreID", "QoreID", "identity", "Identity and business verification APIs for West African onboarding.", "https://docs.qoreid.com", "Per-verification pricing", ["NG", "GH", "KE"]),
    ("Peleza", "Peleza International", "identity", "Background checks and ID verification for East African employers.", "https://peleza.com", "Per-check pricing", ["KE", "UG", "TZ", "RW"]),
    ("MetaMap", "MetaMap", "identity", "Global identity verification with strong coverage of African documents.", "https://docs.metamap.com", "Per-verification pricing", ["NG", "KE", "GH", "ZA", "CM"]),
    ("Verified.ng", "Verified", "identity", "NIN, BVN, CAC and vehicle checks through a single Nigerian API.", "https://verified.ng/docs", "Pay-as-you-go", ["NG"]),
    # Localization
    ("Mapbox Maps SDK", "Mapbox", "localization", "Vector maps, geocoding and routing with offline support for low bandwidth.", "https://docs.mapbox.com", "Free tier then usage based", ["KE", "NG", "ZA", "GH", "CM", "SN"]),
    ("HERE Maps API", "HERE Technologies", "localization", "Geocoding, routing and map tiles with African road coverage.", "https://www.here.com/docs", "Free tier then usage based", ["ZA", "KE", "NG", "GH"]),
    ("OpenStreetMap Nominatim", "OpenStreetMap Foundation", "localization", "Open geocoding and reverse geocoding built on community map data.", "https://nominatim.org/release-docs/latest/api/Overview", "Free with usage policy", ["CM", "NG", "KE", "GH", "SN", "CI", "ZA", "RW"]),
    ("what3words", "what3words", "localization", "Three-word addresses for locations without formal street addressing.", "https://developer.what3words.com", "Free tier then per request", ["ZA", "NG", "KE", "GH", "CM"]),
    ("Plus Codes", "Google Open Source", "localization", "Open location code system that turns coordinates into short addresses.", "https://github.com/google/open-location-code", "Open source / free", ["CM", "NG", "KE", "GH", "SN", "CI", "ZA", "RW"]),
    ("Geoapify", "Geoapify", "localization", "Geocoding, isochrones and address autocomplete with a free tier.", "https://apidocs.geoapify.com", "Free tier then usage based", ["ZA", "NG", "KE"]),
    ("TomTom Location APIs", "TomTom", "localization", "Search, routing and traffic APIs with African city coverage.", "https://developer.tomtom.com", "Free tier then usage based", ["ZA", "KE", "NG", "GH"]),
    ("Loqate Address Validation", "GBG", "localization", "Address capture and validation for African delivery and onboarding flows.", "https://www.loqate.com/resources/support/apis", "Per-lookup pricing", ["ZA", "NG", "KE", "GH"]),
    # Languages
    ("Google Cloud Translation", "Google", "languages", "Machine translation with African language pairs and glossary support.", "https://cloud.google.com/translate/docs", "Per-character pricing", ["ZA", "NG", "KE", "GH", "CM", "SN", "CI", "RW"]),
    ("Hugging Face Inference API", "Hugging Face", "languages", "Hosted inference for African language models published by the community.", "https://huggingface.co/docs/api-inference", "Free tier then usage based", ["NG", "KE", "ZA", "GH"]),
    ("Mozilla Common Voice", "Mozilla Foundation", "languages", "Open speech datasets in African languages for training ASR models.", "https://commonvoice.mozilla.org/datasets", "Open data / free", ["CM", "KE", "ZA", "RW", "NG"]),
    ("NLLB-200", "Meta AI", "languages", "Open multilingual translation model covering dozens of African languages.", "https://github.com/facebookresearch/fairseq/tree/nllb", "Open source / free", ["CM", "NG", "KE", "ZA", "SN", "CI", "RW", "GH"]),
    ("GhanaNLP", "GhanaNLP", "languages", "Open datasets and models for Twi, Ewe, Ga and Dagbani.", "https://ghananlp.org", "Open source / free", ["GH"]),
    ("SADiLaR", "South African Centre for Digital Language Resources", "languages", "Corpora, lexica and tools for South African languages.", "https://sadilar.org", "Open data / free", ["ZA"]),
    ("DeepL API", "DeepL", "languages", "High-quality translation with glossary and document support.", "https://developers.deepl.com", "Free tier then per character", ["ZA", "NG", "KE"]),
]

PROBLEM_TEMPLATES = [
    ("MTN MoMo sandbox returns 401 on collections", "payments", "Python"),
    ("Orange Money callback signature never validates", "payments", "Node.js"),
    ("Wave checkout fails on Safari iOS", "payments", "React"),
    ("Flutterwave webhook duplicates payments", "billing", "FastAPI"),
    ("Paystack transfer recipients rejected for Ghana", "payments", "TypeScript"),
    ("Africa's Talking USSD session times out early", "communication", "Python"),
    ("Termii OTP delivery delayed on MTN Nigeria", "communication", "Node.js"),
    ("Smile ID document upload rejects Cameroonian CNI", "identity", "Flutter"),
    ("Google Maps geocoding returns wrong Yaounde district", "localization", "JavaScript"),
    ("Masakhane model tokenizer breaks on Yoruba diacritics", "languages", "Python"),
    ("PostgreSQL connection pool exhausted under FastAPI", "backend", "FastAPI"),
    ("Docker image fails health check on ARM servers", "devops", "Docker"),
    ("React Native build fails on Android 14", "mobile", "React Native"),
    ("Tailwind dark mode flashes on first paint", "frontend", "React"),
    ("Async SQLAlchemy sessions leak in background tasks", "backend", "Python"),
    ("Mobile money reconciliation mismatch after retries", "payments", "Python"),
    ("Offline-first sync conflicts in Flutter apps", "mobile", "Flutter"),
    ("SMS OTP abuse via leaked verification endpoint", "security", "Node.js"),
    ("CORS blocks cookie auth on mobile webviews", "frontend", "TypeScript"),
    ("Alembic migration locks table during deploy", "devops", "PostgreSQL"),
    ("KYC liveness check fails on low-end devices", "identity", "Android"),
    ("Flutterwave split payments rounding errors", "billing", "Python"),
    ("Redis rate limiter counts health checks", "backend", "Go"),
    ("French accents corrupted in SMS encoding", "localization", "Python"),
    ("GitHub Actions cache misses on monorepo builds", "devops", "TypeScript"),
]

SOLUTION_TEXTS = [
    "The API requires an explicit subscription key per product and a fresh access token per request. Cache the token for 50 minutes, send the subscription key alongside it, and never reuse the sandbox token across environments.",
    "Normalise the raw body before hashing: some gateways re-serialise JSON. Compute HMAC-SHA256 over the exact received bytes, compare with hmac.compare_digest, and reject requests older than five minutes.",
    "Safari blocks third-party cookies inside the payment iframe. Redirect top-level instead of embedding, and keep the return URL on the same registrable domain to preserve the session cookie.",
    "Webhook retries are part of the contract. Store the provider event id in a unique column, process inside a transaction and return 200 only after commit. Duplicates then become cheap no-ops.",
    "Ghana recipients need a bank_code and a validated mobile-money network prefix. Validate with the bank list endpoint first and cache the mapping for a day.",
    "USSD gateways end the session after a short idle period. Keep each menu response under 180 characters, answer within 3 seconds and always end with a choice prompt so the aggregator keeps the session alive.",
    "Sender IDs must be pre-approved per network; unregistered IDs are silently dropped on MTN. Register the sender ID and switch to a fallback route for OTP traffic.",
    "The document type must match the country's accepted list. Cameroonian CNI needs the CNI type and a JPEG under 2 MB; convert HEIC uploads server-side before submitting.",
    "Use components=country:CM and add the city plus district to the query. Google returns locality-level results for many African addresses, so parse address_components rather than formatted strings.",
    "Normalise Unicode to NFC before tokenisation and keep diacritics. If the tokenizer was trained without them, add a deterministic transliteration step and evaluate on a held-out set.",
    "Create the async engine once per process, size the pool to workers * 2 + 1, and always release sessions with async with. Long-running tasks should borrow a fresh session, not reuse request-scoped ones.",
    "The base image's health check binary is architecture-specific. Install curl in the runtime image or use a Python one-liner, then set --platform=linux/arm64 explicitly in CI.",
    "Android 14 requires explicit android:exported attributes and JDK 17. Upgrade the Gradle plugin, set the compile SDK to 34 and rebuild the splash screen assets.",
    "Apply the saved theme before React mounts with a small inline script that reads localStorage and sets the dark class on <html>, avoiding a flashed default theme.",
    "Commit inside the request scope or explicitly close the session. Background tasks must open their own session with async with SessionLocal() and handle rollback on error.",
    "Reconciliation compares provider statements against ledger entries. Persist the provider reference for each retry, compare by reference rather than amount, and quarantine unmatched rows for manual review.",
    "Use a per-record revision counter and last-write-wins only for non-conflicting fields. Conflict resolution for text fields should keep both versions and surface a merge UI.",
    "Bind OTP requests to a short-lived server-side challenge, rate limit per phone and per IP, and never return whether a number exists. Add a signed nonce to the verification call.",
    "Cookies in webviews need SameSite=None; Secure plus an allowlisted origin. Avoid wildcard CORS with credentials; echo only known origins from configuration.",
    "Run migrations in a separate step before the app starts, add lock_timeout and create indexes concurrently. For large tables use a two-phase expand/contract migration.",
    "Liveness on low-end devices fails under poor lighting. Ask for a short blink sequence, downscale frames to 480p and send a JPEG quality of 0.7 instead of raw frames.",
    "Split payments must sum exactly to the original amount. Allocate with integer minor units, give the remainder to the largest split, and validate totals before creating the charge.",
    "Key the rate limiter by route, not by health checks. Exclude /health and /metrics, and use a per-user key for authenticated routes.",
    "GSM-7 cannot encode accented French characters consistently. Send UCS-2 when non-GSM characters are present and account for the reduced per-segment length.",
    "Cache the package manager store and key it on the lockfile hash. Split restore/save steps and avoid caching node_modules in a monorepo; cache the package manager's global store instead.",
]


def demo_tag(text: str) -> str:
    return f"[{SEED_LABEL}] {text}"


async def reset_demo(db) -> None:
    demo_user_ids = (await db.execute(select(User.id).where(User.is_demo.is_(True)))).scalars().all()
    conversation_ids = (
        (
            await db.execute(
                select(ConversationMember.conversation_id)
                .where(ConversationMember.user_id.in_(demo_user_ids))
                .distinct()
            )
        ).scalars().all()
        if demo_user_ids
        else []
    )
    if conversation_ids:
        await db.execute(delete(Message).where(Message.conversation_id.in_(conversation_ids)))
        await db.execute(
            delete(ConversationMember).where(ConversationMember.conversation_id.in_(conversation_ids))
        )
        await db.execute(delete(Conversation).where(Conversation.id.in_(conversation_ids)))
    await db.execute(delete(ReputationTransaction).where(ReputationTransaction.is_demo.is_(True)))
    await db.execute(delete(APIEntry).where(APIEntry.is_demo.is_(True)))
    if demo_user_ids:
        await db.execute(delete(User).where(User.id.in_(demo_user_ids)))
    await db.commit()


async def seed_countries(db) -> dict[str, Country]:
    existing = {country.code: country for country in (await db.execute(select(Country))).scalars().all()}
    countries: dict[str, Country] = {}
    for code, name, name_fr, flag in COUNTRIES:
        country = existing.get(code)
        if country is None:
            country = Country(code=code, name=name, name_fr=name_fr, flag_emoji=flag, activity_score=0)
            db.add(country)
        countries[code] = country
    await db.commit()
    for country in countries.values():
        await db.refresh(country)
    return countries


async def seed_users(db, countries: dict[str, Country]) -> list[User]:
    users: list[User] = []
    codes = list(countries)
    for index in range(60):
        first = FIRST_NAMES[index % len(FIRST_NAMES)]
        last = LAST_NAMES[(index * 7) % len(LAST_NAMES)]
        code = codes[index % len(codes)]
        username = f"demo-{first.lower()}-{last.lower().replace(' ', '')}-{index + 1}"
        country = countries[code]
        user = User(
            username=username,
            full_name=f"{first} {last}",
            email=f"{username}@example.invalid",
            bio=demo_tag(
                f"{'Developpeur' if index % 2 else 'Developer'} working on {RNG.choice(SKILLS)} "
                f"in {country.name}."
            ),
            city=RNG.choice(CITIES[code]),
            country_id=country.id,
            github_url=f"https://github.com/{username}",
            is_demo=True,
            reputation_points=0,
            level="newcomer",
        )
        # Backdate accounts so demo signals satisfy the eligibility rules.
        user.created_at = datetime.now(UTC) - timedelta(days=RNG.randint(45, 420))
        user.roles = [UserRole(role="developer"), UserRole(role="project_creator")]
        if index < 15:
            user.roles.append(UserRole(role="company"))
        if index > 53:
            user.roles.append(UserRole(role="api_provider"))
        user.skills = [
            UserSkill(
                name=skill,
                level=RNG.choice(["beginner", "intermediate", "advanced"]),
                years_experience=RNG.randint(1, 8),
            )
            for skill in RNG.sample(SKILLS, k=3)
        ]
        db.add(user)
        users.append(user)

    admin = User(
        username="demo-admin",
        full_name="Demo Administrator",
        bio=demo_tag("Platform administrator account for demonstrations."),
        country_id=countries["CM"].id,
        is_demo=True,
        is_admin=True,
    )
    admin.roles = [UserRole(role="developer"), UserRole(role="admin")]
    admin.skills = [UserSkill(name="Python", level="advanced", years_experience=7)]
    db.add(admin)
    users.append(admin)
    await db.commit()
    return users


async def seed_api_entries(db, users: list[User]) -> list[APIEntry]:
    entries: list[APIEntry] = []
    for index, (name, provider, category, description, docs, pricing, country_codes) in enumerate(API_ENTRIES):
        entry = APIEntry(
            owner_id=users[index % 15].id,
            name=name,
            provider_name=provider,
            slug=name.lower().replace("'", "").replace(" ", "-").replace(".", ""),
            description=demo_tag(description),
            category=category,
            countries=country_codes,
            documentation_url=docs,
            pricing=pricing,
            api_status="operational",
            integration_notes=demo_tag("Sandbox credentials available to registered developers."),
            is_demo=True,
        )
        db.add(entry)
        entries.append(entry)
    await db.commit()
    return entries


async def seed_projects(db, users: list[User], countries: dict[str, Country]) -> list[Project]:
    projects: list[Project] = []
    modes = [
        CollaborationMode.SHOWCASE,
        CollaborationMode.FEEDBACK,
        CollaborationMode.OPEN_TO_CONTRIBUTORS,
    ]
    for index, name in enumerate(PROJECT_NAMES):
        creator = users[index % 40]
        code = RNG.choice(list(countries))
        mode = modes[index % 3]
        project = await project_service.create_project(
            db,
            creator,
            ProjectCreate(
                name=name,
                description=demo_tag(
                    f"{name} helps developers and small businesses in {countries[code].name} "
                    f"ship reliable software. Built with {', '.join(TECH_STACKS[index % len(TECH_STACKS)])}. "
                    "This project is part of the demonstration dataset."
                ),
                repository_url=f"https://github.com/afridev-demo/{name.lower()}",
                demo_url=f"https://demo.afridev.example/{name.lower()}",
                technologies=TECH_STACKS[index % len(TECH_STACKS)],
                tags=[CATEGORIES[index % len(CATEGORIES)], "demo"],
                category=CATEGORIES[index % len(CATEGORIES)],
                country_code=code,
                collaboration_mode=mode,
            ),
        )
        project.is_demo = True
        project.github_stars = RNG.randint(0, 320)
        project.view_count = RNG.randint(5, 900)
        project.ownership_status = "verified" if index % 4 == 0 else "pending"
        projects.append(project)
    await db.commit()

    for project in projects:
        candidates = [user for user in users[:55] if user.id != project.creator_id]
        for fan in RNG.sample(candidates, k=RNG.randint(6, 18)):
            db.add(ProjectLike(project_id=project.id, user_id=fan.id, is_demo=True))
        for passer in RNG.sample(candidates, k=RNG.randint(2, 6)):
            db.add(ProjectPass(project_id=project.id, user_id=passer.id, is_demo=True))
    await db.commit()
    return projects


async def seed_knowledge(db, users: list[User], countries: dict[str, Country], api_entries: list[APIEntry]):
    problems: list[KnowledgeProblem] = []
    codes = list(countries)
    for index in range(25):
        template_title, category, technology = PROBLEM_TEMPLATES[index % len(PROBLEM_TEMPLATES)]
        code = codes[index % len(codes)]
        author = users[(index * 3) % 50]
        problem = await knowledge_service.create_problem(
            db,
            author,
            ProblemCreate(
                title=demo_tag(f"{template_title} ({countries[code].code})"),
                description=demo_tag(
                    "Contexte terrain : "
                    f"{template_title}. L'integration echoue de facon intermittente en production, "
                    "alors que le sandbox fonctionne. Les journaux montrent des reponses incoherentes "
                    "et un comportement different selon l'operateur mobile. "
                    "Ce probleme fait partie du jeu de demonstration."
                ),
                category=category,
                technology=technology,
                country_code=code,
                api_entry_id=api_entries[index % len(api_entries)].id,
                code_snippet="async def charge(payload):\n    return await client.post('/collections', json=payload)",
                documentation_links=[api_entries[index % len(api_entries)].documentation_url],
            ),
        )
        problem.is_demo = True
        problems.append(problem)
    await db.commit()

    solutions: list[tuple[KnowledgeProblem, Solution]] = []
    for index in range(45):
        problem = problems[index % len(problems)]
        author = users[(index * 5 + 7) % 50]
        if author.id == problem.author_id:
            author = users[(index * 5 + 8) % 50]
        solution = await knowledge_service.add_solution(
            db,
            problem,
            author,
            SolutionCreate(
                explanation=demo_tag(SOLUTION_TEXTS[index % len(SOLUTION_TEXTS)]),
                code_snippet="# demo snippet\nresponse = await client.post(url, json=payload, headers=headers)",
                implementation_steps=demo_tag(
                    "1. Reproduce\n2. Patch\n3. Validate in sandbox\n4. Deploy"
                ),
                references=[api_entries[index % len(api_entries)].documentation_url],
            ),
        )
        solution.is_demo = True
        solutions.append((problem, solution))
    await db.commit()
    return problems, solutions


async def seed_accepted_work(db, users: list[User], solutions) -> list:
    accepted = []
    seen_problems: set = set()
    for problem, solution in solutions:
        if len(accepted) >= 15:
            break
        if problem.id in seen_problems:
            continue
        seen_problems.add(problem.id)
        author = next(user for user in users if user.id == problem.author_id)
        try:
            result = await knowledge_service.accept_solution(db, problem, solution, author)
        except Exception as exc:  # pragma: no cover - defensive during seeding
            print(f"  skipped acceptance: {exc}")
            continue
        accepted.append((problem, result))
    return accepted


async def seed_confirmations(db, users: list[User], accepted) -> int:
    count = 0
    for index, (_problem, solution) in enumerate(accepted):
        report = (
            await db.execute(select(FieldReport).where(FieldReport.solution_id == solution.id))
        ).scalar_one_or_none()
        if report is None:
            continue
        candidates = [
            user
            for user in users[:55]
            if user.country_id == report.country_id and user.id != report.author_id
        ]
        if len(candidates) < 2:
            continue
        for confirmer in RNG.sample(candidates, k=min(len(candidates), 2 + (index % 2))):
            try:
                await field_report_service.confirm_report(
                    db, report, confirmer, comment=demo_tag("Confirme sur le terrain.")
                )
                count += 1
            except Exception:
                continue
    return count


async def seed_missions(db, users: list[User], countries: dict[str, Country], api_entries: list[APIEntry]) -> list[Mission]:
    missions: list[Mission] = []
    codes = list(countries)
    for index in range(15):
        sponsor = users[index % 15]
        entry = api_entries[index % len(api_entries)]
        code = codes[index % len(codes)]
        mission = Mission(
            sponsor_id=sponsor.id,
            api_entry_id=entry.id,
            country_id=countries[code].id,
            title=demo_tag(f"Integrate {entry.name} for {countries[code].name} merchants"),
            slug=f"demo-mission-{index + 1}",
            description=demo_tag(
                f"Build a reference integration of {entry.name} covering collections, "
                "error handling and reconciliation. Deliverables are reviewed manually."
            ),
            objectives=demo_tag("Publish a working sandbox integration, a README and 3 field notes."),
            required_skills=["Python", "REST APIs", "Testing"],
            reward_points=30,
            reward_description="30 reputation points and public recognition",
            deadline=datetime.now(UTC) + timedelta(days=14 + index),
            status=MissionStatus.PUBLISHED.value,
            is_demo=True,
        )
        db.add(mission)
        missions.append(mission)
    await db.commit()
    return missions


async def seed_mission_submissions(db, users: list[User], missions: list[Mission]) -> int:
    count = 0
    for index, mission in enumerate(missions[:8]):
        developer = users[(index * 4 + 20) % 50]
        if developer.id == mission.sponsor_id:
            continue
        db.add(
            MissionSubmission(
                mission_id=mission.id,
                developer_id=developer.id,
                summary=demo_tag("Integration completed with sandbox tests and a short field report."),
                solution_url=f"https://github.com/afridev-demo/mission-{index + 1}",
                status="under_review",
                is_demo=True,
            )
        )
        count += 1
    await db.commit()
    return count


async def seed_contributions(db, users: list[User], projects: list[Project]) -> int:
    open_projects = [
        project
        for project in projects
        if project.collaboration_mode == CollaborationMode.OPEN_TO_CONTRIBUTORS.value
    ]
    accepted = 0
    for index, project in enumerate(open_projects[:10]):
        requester = users[(index * 3 + 5) % 50]
        if requester.id == project.creator_id:
            requester = users[(index * 3 + 6) % 50]
        try:
            request = await contribution_service.create_request(
                db,
                project,
                requester,
                ContributionCreate(
                    message=demo_tag(
                        f"I can help with {RNG.choice(list(ContributionDomain)).value}. "
                        "I have shipped similar integrations and can document the pitfalls."
                    ),
                    domain=RNG.choice(list(ContributionDomain)),
                ),
            )
        except Exception:
            continue
        if index < 8:
            maintainer = await db.get(User, project.creator_id)
            await contribution_service.accept_request(db, request, maintainer)
            accepted += 1
            if index < 3:
                await contribution_service.mark_merged(db, request, maintainer)
    return accepted


async def seed_solution_votes(db, users: list[User], solutions) -> int:
    """Community usefulness votes, which drive the +2/+10 reputation rule."""
    count = 0
    for index, (_problem, solution) in enumerate(solutions[:12]):
        for offset in range(3):
            voter = users[(index * 7 + offset + 3) % 55]
            if voter.id == solution.author_id:
                continue
            try:
                await knowledge_service.vote_solution(db, solution, voter)
                count += 1
            except Exception:
                continue
    return count


async def mark_stale_reports(db) -> int:
    """Age a few reports so the 90-day revalidation state is visible in the demo."""
    reports = (
        (await db.execute(select(FieldReport).order_by(FieldReport.created_at).limit(6)))
        .scalars()
        .all()
    )
    for report in reports[:4]:
        report.last_validated_at = datetime.now(UTC) - timedelta(days=120)
    await db.commit()
    return await field_report_service.flag_stale_reports(db)


async def seed_feedback(db, users: list[User], projects: list[Project]) -> int:
    feedback_projects = [
        project for project in projects if project.collaboration_mode == CollaborationMode.FEEDBACK.value
    ]
    created = 0
    for index, project in enumerate(feedback_projects):
        for offset in range(2):
            author = users[(index * 2 + offset + 11) % 50]
            if author.id == project.creator_id:
                continue
            existing = (
                await db.execute(
                    select(ProjectFeedback).where(
                        ProjectFeedback.project_id == project.id,
                        ProjectFeedback.author_id == author.id,
                    )
                )
            ).scalar_one_or_none()
            if existing:
                continue
            feedback = await project_service.add_feedback(
                db,
                project,
                author,
                demo_tag("Strong concept with a clear local use case."),
                demo_tag("Improve onboarding and document offline behaviour."),
                demo_tag("A dashboard for weekly reconciliation would help."),
            )
            feedback.is_demo = True
            created += 1
            if offset == 0:
                maintainer = await db.get(User, project.creator_id)
                await project_service.mark_feedback_useful(db, feedback, maintainer)
    return created


async def update_activity_scores(db) -> None:
    for country in (await db.execute(select(Country))).scalars().all():
        developers = int(
            (
                await db.execute(
                    select(func.count(User.id)).where(
                        User.country_id == country.id, User.is_demo.is_(True)
                    )
                )
            ).scalar_one()
        )
        reports = int(
            (
                await db.execute(
                    select(func.count(FieldReport.id)).where(
                        FieldReport.country_id == country.id, FieldReport.is_demo.is_(True)
                    )
                )
            ).scalar_one()
        )
        country.activity_score = developers * 10 + reports * 5


async def summarise(db) -> None:
    async def count(model, *conditions) -> int:
        stmt = select(func.count()).select_from(model)
        if conditions:
            stmt = stmt.where(*conditions)
        return int((await db.execute(stmt)).scalar_one())

    print("\nDemo dataset ready:")
    print(f"  countries      : {await count(Country)}")
    print(f"  demo users     : {await count(User, User.is_demo.is_(True))}")
    print(f"  demo projects  : {await count(Project, Project.is_demo.is_(True))}")
    print(f"  problems       : {await count(KnowledgeProblem, KnowledgeProblem.is_demo.is_(True))}")
    print(f"  solutions      : {await count(Solution, Solution.is_demo.is_(True))}")
    print(f"  field reports  : {await count(FieldReport)}")
    print(f"  missions       : {await count(Mission, Mission.is_demo.is_(True))}")
    print(f"  API entries    : {await count(APIEntry, APIEntry.is_demo.is_(True))}")
    print(f"  contributions  : {await count(ContributionRequest)}")
    print(f"  conversations  : {await count(Conversation)}")
    print(f"  ledger rows    : {await count(ReputationTransaction, ReputationTransaction.is_demo.is_(True))}")
    print("\nAll demo content is flagged is_demo=True and displays a [DEMO] label.")


async def run(reset: bool) -> None:
    async with SessionLocal() as db:
        if reset:
            print("Resetting demo data (real records are preserved)...")
            await reset_demo(db)

        existing = int(
            (await db.execute(select(func.count(User.id)).where(User.is_demo.is_(True)))).scalar_one()
        )
        if existing:
            print(f"Demo data already present ({existing} demo users). Use --reset to regenerate.")
            await summarise(db)
            return

        countries = await seed_countries(db)
        users = await seed_users(db, countries)
        print(f"  users created: {len(users)}")
        api_entries = await seed_api_entries(db, users)
        projects = await seed_projects(db, users, countries)
        print(f"  projects created: {len(projects)}")
        problems, solutions = await seed_knowledge(db, users, countries, api_entries)
        print(f"  problems: {len(problems)}, solutions: {len(solutions)}")
        accepted = await seed_accepted_work(db, users, solutions)
        confirmations = await seed_confirmations(db, users, accepted)
        votes = await seed_solution_votes(db, users, solutions)
        stale = await mark_stale_reports(db)
        print(
            f"  accepted solutions: {len(accepted)}, confirmations: {confirmations}, "
            f"useful votes: {votes}, flagged for revalidation: {stale}"
        )
        missions = await seed_missions(db, users, countries, api_entries)
        submissions = await seed_mission_submissions(db, users, missions)
        contributions = await seed_contributions(db, users, projects)
        feedback = await seed_feedback(db, users, projects)
        print(
            f"  missions: {len(missions)}, submissions: {submissions}, "
            f"accepted contributions: {contributions}, feedback: {feedback}"
        )
        await update_activity_scores(db)
        await db.commit()
        await reputation_service.recalculate_all(db)
        await summarise(db)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed deterministic AfriDev Hub demo data")
    parser.add_argument("--reset", action="store_true", help="Remove demo records before seeding")
    args = parser.parse_args()
    asyncio.run(run(args.reset))


if __name__ == "__main__":
    main()
