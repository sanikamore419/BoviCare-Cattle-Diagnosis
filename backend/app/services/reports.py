import json
import os
from io import BytesIO
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from app.core.time import as_utc
from app.models import Cattle, ClinicalCase, NotificationLog, PredictionResult, User


_MARATHI_FONT = "BoviCareMarathi"
_MARATHI_FONT_PATHS = [
    Path(r"C:\Windows\Fonts\Nirmala.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf"),
    Path("/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf"),
]

_DISEASE_MARATHI = {
    "HEALTHY": "निरोगी (Healthy)",
    "LSD": "लम्पी स्किन डिसीज (LSD)",
    "RINGWORM": "रिंगवर्म (Ringworm)",
    "FMD": "फूट-अँड-माउथ डिसीज (FMD)",
    "Lumpy Skin": "लम्पी स्किन (Lumpy Skin)",
    "Normal Skin": "सामान्य त्वचा (Normal Skin)",
    "foot-and-mouth": "फूट-अँड-माउथ डिसीज (Foot-and-mouth)",
    "foot_and_mouth": "फूट-अँड-माउथ डिसीज (Foot and mouth)",
    "mastitis": "स्तनदाह (mastitis)",
    "Mastitis": "स्तनदाह (Mastitis)",
    "No Mastitis": "No Mastitis",
}

_SYMPTOM_MARATHI = {
    "loss of appetite": "भूक न लागणे",
    "lethargy": "सुस्ती",
    "weight loss": "वजन कमी होणे",
    "coughing": "खोकला",
    "difficulty breathing": "श्वास घेण्यास त्रास",
    "nasal discharge": "नाकातून स्राव",
    "diarrhea": "जुलाब",
    "bloating": "पोट फुगणे",
    "reduced rumination": "रवंथ कमी होणे",
    "cannot stand": "उभे राहता न येणे",
    "seizure": "आकडी येणे",
    "severe bleeding": "जास्त रक्तस्राव",
}

_RISK_MARATHI = {"high": "जास्त", "moderate": "मध्यम", "medium": "मध्यम", "low": "कमी"}
_RISK_ENGLISH = {"high": "High", "moderate": "Moderate", "medium": "Moderate", "low": "Low"}


def _display_disease(label: str, language: str) -> str:
    if language == "mr":
        return _DISEASE_MARATHI.get(label, label.replace("_", " "))
    if label in {"LSD", "FMD", "IBK"}:
        return label
    if label.isupper():
        return label.title()
    return label.replace("_", " ").replace("-", " ").title()


def _display_symptom(label: str, language: str) -> str:
    if language == "en":
        return label.replace("_", " ").capitalize()
    return _SYMPTOM_MARATHI.get(label.lower(), label.replace("_", " ").capitalize())


def _display_risk(level: str, language: str) -> str:
    values = _RISK_MARATHI if language == "mr" else _RISK_ENGLISH
    return values.get(level.lower(), values["moderate"])


def _format_probability(probability: float) -> str:
    percentage = Decimal(str(probability)) * 100
    formatted = format(percentage, "f")
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return f"{formatted}%"


def _register_marathi_font() -> str:
    if _MARATHI_FONT in pdfmetrics.getRegisteredFontNames():
        return _MARATHI_FONT
    configured_path = os.environ.get("BOVICARE_MARATHI_FONT")
    candidates = ([Path(configured_path)] if configured_path else []) + _MARATHI_FONT_PATHS
    font_path = next((path for path in candidates if path.is_file()), None)
    if font_path is None:
        raise RuntimeError("A Devanagari TrueType font is required for farmer PDF reports.")
    options = {"shapable": True}
    if font_path.suffix.lower() == ".ttc":
        options["subfontIndex"] = 0
    pdfmetrics.registerFont(TTFont(_MARATHI_FONT, str(font_path), **options))
    return _MARATHI_FONT


def _farmer_report(case: ClinicalCase, db, language: str) -> bytes:
    is_marathi = language == "mr"
    font = _register_marathi_font() if is_marathi else "Helvetica"
    labels = {
        "title": "जनावराच्या तपासणीचा अहवाल" if is_marathi else "Cattle Diagnostic Report",
        "cattle": "जनावराची माहिती" if is_marathi else "Cattle Information",
        "tag": "टॅग क्रमांक" if is_marathi else "Tag Number",
        "date": "तारीख" if is_marathi else "Date",
        "symptoms": "नोंदवलेली लक्षणे" if is_marathi else "Reported Symptoms",
        "result": "तपासणीचा निकाल" if is_marathi else "Diagnosis Result",
        "general": "लक्षणांवर आधारित संभाव्य आजार" if is_marathi else "Possible diseases based on symptoms",
        "milk": "दुधाच्या माहितीवर आधारित अंदाज" if is_marathi else "Estimate based on milk information",
        "image": "फोटोवर आधारित संभाव्य आजार" if is_marathi else "Possible diseases based on image",
        "skin_image": "फोटोवर आधारित त्वचेचा अंदाज" if is_marathi else "Skin estimate based on image",
        "risk": "जोखीम पातळी" if is_marathi else "Risk Level",
        "advice": "काय करावे?" if is_marathi else "What should you do?",
        "vet": "कृपया पशुवैद्यकांचा सल्ला घ्या." if is_marathi else "Please consult a veterinarian.",
        "note": "महत्त्वाची सूचना" if is_marathi else "Important Note",
        "disclaimer": "हा AI आधारित प्राथमिक अंदाज आहे. अंतिम निदान आणि उपचारासाठी पात्र पशुवैद्यकांचा सल्ला घ्या." if is_marathi else "This is an AI-based preliminary result. Final diagnosis and treatment should be confirmed by a qualified veterinarian.",
        "no_symptoms": "लक्षणे नोंदवलेली नाहीत" if is_marathi else "No symptoms reported",
    }
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"BoviCare AI - {labels['title']}")

    rows = db.query(PredictionResult).filter(PredictionResult.case_id == case.id).order_by(
        PredictionResult.model_name, PredictionResult.rank, PredictionResult.created_at.desc()
    ).all()
    grouped = {}
    for row in rows:
        grouped.setdefault(row.model_name, []).append(row)

    def latest_unique_rank(model_name):
        newest = {}
        for row in grouped.get(model_name, []):
            key = row.rank if row.rank is not None else 1
            if key not in newest or row.created_at > newest[key].created_at:
                newest[key] = row
        return [newest[rank] for rank in sorted(newest)[:5]]

    symptoms = json.loads(case.symptoms or "[]")
    symptom_text = ", ".join(_display_symptom(item, language) for item in symptoms) if symptoms else labels["no_symptoms"]
    report_timestamp = as_utc(case.created_at)
    report_date = report_timestamp.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%d-%m-%Y") if report_timestamp else ""
    y = 790

    def draw_line(text, size=11, bold=False, indent=0):
        nonlocal y
        chosen_font = font + ("-Bold" if bold and not is_marathi else "") if not is_marathi else font
        pdf.setFont(chosen_font, size)
        max_width = 490 - indent
        if is_marathi:
            lines = []
            current = ""
            for word in text.split():
                candidate = f"{current} {word}".strip()
                if current and stringWidth(candidate, chosen_font, size) > max_width:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            if current:
                lines.append(current)
        else:
            lines = simpleSplit(text, chosen_font, size, max_width)
        for line in lines:
            if y < 55:
                pdf.showPage()
                y = 790
            pdf.drawString(52 + indent, y, line, shaping=is_marathi)
            y -= size + 6

    def draw_predictions(model_name, heading):
        nonlocal y
        predictions = latest_unique_rank(model_name)
        if not predictions:
            return
        draw_line(heading, 13, True)
        risk = _display_risk(predictions[0].risk_level, language)
        draw_line(f"{labels['risk']}: {risk}", 10)
        for rank, row in enumerate(predictions, 1):
            disease = _display_disease(row.disease_label, language)
            percentage = _format_probability(row.probability)
            draw_line(f"{rank}. {disease} - {percentage}", 11, indent=8)
        y -= 5

    draw_line("BoviCare AI", 20, True)
    draw_line(labels["title"], 16, True)
    y -= 6
    draw_line(labels["cattle"], 13, True)
    draw_line(f"{labels['tag']}: {case.cattle_tag}", 11)
    if report_date:
        draw_line(f"{labels['date']}: {report_date}", 11)
    y -= 5
    draw_line(f"{labels['symptoms']}: {symptom_text}", 11)
    y -= 8
    draw_line(labels["result"], 16, True)
    draw_predictions("general_cattle_disease", labels["general"])
    draw_predictions("mastitis_specialist", labels["milk"])
    draw_predictions("cattle_image_classifier", labels["image"])
    draw_predictions("lumpy_skin_specialist", labels["skin_image"])
    draw_line(labels["advice"], 13, True)
    draw_line(labels["vet"], 11)
    y -= 3
    draw_line(f"{labels['note']}: {labels['disclaimer']}", 10)
    pdf.save()
    return buffer.getvalue()


def build_case_report(case: ClinicalCase, db, farmer_view: bool = False, language: str = "en", *, user_id: int) -> bytes:
    """Generate a factual report from persisted case and prediction data."""
    if farmer_view:
        return _farmer_report(case, db, "mr" if language == "mr" else "en")

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"BoviCare case {case.id}")
    owner = db.get(User, case.owner_id)
    cattle = db.get(Cattle, case.cattle_id) if case.cattle_id else None
    rows = db.query(PredictionResult).filter(PredictionResult.case_id == case.id).order_by(PredictionResult.model_name, PredictionResult.rank).all()
    notifications = db.query(NotificationLog).filter(NotificationLog.case_id == case.id, NotificationLog.user_id == user_id).order_by(NotificationLog.created_at).all()
    grouped = {}
    for row in rows:
        grouped.setdefault(row.model_name, []).append(row)

    cattle_record = "Not available"
    if cattle:
        cattle_record = cattle.name or cattle.tag_number
    breed = case.breed or (cattle.breed if cattle else None) or "Not provided"
    lines = [
        "BoviCare AI - Diagnostic Case Report",
        f"Case ID: {case.id}",
        "",
        "Cattle information",
        f"Tag: {case.cattle_tag}",
        f"Cattle record: {cattle_record}",
        f"Breed: {breed}",
        f"Age (years): {case.age_years if case.age_years is not None else 'Not provided'}",
        f"Sex: {cattle.sex if cattle else 'Not available'}",
        "",
        "Farmer information",
        f"Name: {owner.full_name if owner else 'Not available'}",
        f"Email: {owner.email if owner else 'Not available'}",
        "",
        "Submitted clinical information",
        f"Symptoms: {', '.join(json.loads(case.symptoms))}",
        f"Temperature: {case.temperature_c if case.temperature_c is not None else 'Not provided'}",
        f"Review status: {case.status}",
        f"Veterinarian notes: {case.veterinarian_notes or 'Not provided'}",
        f"High-risk notifications: {', '.join(log.status for log in notifications) if notifications else 'None'}",
        "",
        "AI model results",
    ]
    model_labels = {
        "general_cattle_disease": "Model A - General cattle disease",
        "mastitis_specialist": "Model B - Mastitis specialist",
        "cattle_image_classifier": "Model C - Cattle image classifier",
        "lumpy_skin_specialist": "Model D - Lumpy skin specialist",
    }
    for model_name, title in model_labels.items():
        model_rows = grouped.get(model_name, [])
        lines.append(title)
        if not model_rows:
            lines.append("Result: Not available for this case")
            continue
        lines.append(f"Risk level: {model_rows[0].risk_level}")
        for row in model_rows:
            rank = f"Rank {row.rank}: " if row.rank is not None else "Result: "
            lines.append(f"{rank}{row.disease_label} ({row.probability * 100:.1f}%)")
    lines.extend([
        "",
        "Disclaimer: AI output is decision support only and requires confirmation by a qualified veterinarian.",
    ])

    y = 800
    for index, line in enumerate(lines):
        heading = index == 0 or line in {"Cattle information", "Farmer information", "Submitted clinical information", "AI model results"} or line.startswith("Model ")
        font = "Helvetica-Bold" if heading else "Helvetica"
        size = 14 if index == 0 else 10
        for part in simpleSplit(line, font, size, 495):
            if y < 55:
                pdf.showPage()
                y = 800
            pdf.setFont(font, size)
            pdf.drawString(50, y, part)
            y -= 15
    pdf.save()
    return buffer.getvalue()
