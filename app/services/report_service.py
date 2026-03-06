import os
import re
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


REPORTS_DIR = "generated_reports"


def _ensure_reports_dir():
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:80].strip("-")


def build_pdf_report(topic: str, days_back: int, summary_data: dict) -> str:
    _ensure_reports_dir()

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"report-{_slugify(topic)}-{timestamp}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=2.1 * cm,
        rightMargin=2.1 * cm,
        topMargin=2.0 * cm,
        bottomMargin=1.8 * cm,
        title=f"Informe - {topic}",
        author="analisisNoticias",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#16324F"),
        spaceAfter=10,
        alignment=TA_LEFT,
    )

    subtitle_style = ParagraphStyle(
        "SubtitleCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#5B6573"),
        spaceAfter=12,
    )

    section_style = ParagraphStyle(
        "SectionCustom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#16324F"),
        spaceBefore=10,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.2,
        leading=14.2,
        textColor=colors.HexColor("#1F2933"),
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "BulletCustom",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=5,
    )

    small_style = ParagraphStyle(
        "SmallCustom",
        parent=body_style,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#52606D"),
    )

    story = []

    # Encabezado
    story.append(Paragraph("Informe de análisis de noticias", title_style))
    story.append(
        Paragraph(
            f"Tema: {topic}<br/>"
            f"Ventana analizada: últimos {days_back} días<br/>"
            f"Fecha de emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D9E2EC")))
    story.append(Spacer(1, 0.25 * cm))

    # Resumen ejecutivo
    story.append(Paragraph("Resumen ejecutivo", section_style))
    story.append(Paragraph(summary_data.get("executive_summary", ""), body_style))

    # Puntos clave
    key_points = summary_data.get("key_points", [])
    if key_points:
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph("Puntos clave", section_style))
        for item in key_points:
            story.append(Paragraph(f"• {item}", bullet_style))

    # Tendencias
    trends = summary_data.get("repeated_trends", [])
    if trends:
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph("Tendencias observadas", section_style))
        for item in trends:
            story.append(Paragraph(f"• {item}", bullet_style))

    # Noticias relevantes
    relevant_articles = summary_data.get("relevant_articles", [])
    if relevant_articles:
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph("Noticias más relevantes", section_style))

        table_data = [
            [
                Paragraph("<b>Título</b>", small_style),
                Paragraph("<b>Fuente / Fecha</b>", small_style),
                Paragraph("<b>Por qué importa</b>", small_style),
            ]
        ]

        for article in relevant_articles[:5]:
            title = article.get("title", "")
            source = article.get("source", "")
            published = article.get("published", "")
            why = article.get("why_relevant", "")

            table_data.append(
                [
                    Paragraph(title, body_style),
                    Paragraph(f"{source}<br/>{published}", small_style),
                    Paragraph(why, body_style),
                ]
            )

        table = Table(
            table_data,
            colWidths=[7.0 * cm, 3.5 * cm, 6.0 * cm],
            repeatRows=1,
            hAlign="LEFT",
        )

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF2F8")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#16324F")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                    ("LEADING", (0, 0), (-1, -1), 12),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, 0), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E2EC")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFBFC")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )

        story.append(table)

    # Nota final
    story.append(Spacer(1, 0.35 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D9E2EC")))
    story.append(Spacer(1, 0.15 * cm))
    story.append(
        Paragraph(
            "Informe generado automáticamente a partir de noticias recolectadas y sintetizadas mediante IA.",
            small_style,
        )
    )

    doc.build(story)
    return filepath