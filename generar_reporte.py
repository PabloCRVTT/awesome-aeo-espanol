#!/usr/bin/env python3
"""Genera un reporte AEO profesional en PDF a partir del crawler de VisibleAI."""

import os
import sys
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from crawler import analyze_d1, analyze_d2, extract_main_text, fetch_html


BLACK = HexColor("#111110")
LIME = HexColor("#b8e800")
GRAY = HexColor("#888880")
WHITE = white
LIGHT_GRAY = HexColor("#f4f4f1")
RED = HexColor("#d23a3a")
AMBER = HexColor("#e8a800")

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


# ---------- Helpers ----------

def wrap_text(text, font_name, font_size, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def format_date_es(dt):
    return f"{dt.day} de {MESES_ES[dt.month - 1]} de {dt.year}"


def finding_marker(finding):
    upper = finding.upper()
    if upper.startswith("OK"):
        return "check", finding[2:].strip()
    if upper.startswith("FALTA"):
        return "cross", finding[5:].strip()
    if upper.startswith("PARCIAL"):
        return "warn", finding[7:].strip()
    if upper.startswith("ERROR"):
        return "cross", finding[5:].strip()
    return "neutral", finding


def generate_recommendations(d1, d2):
    """Replica la priorizacion de print_report en crawler.py."""
    recs = []
    for f in d1["findings"]:
        if f.startswith("FALTA") or f.startswith("PARCIAL"):
            if "JSON-LD" in f:
                recs.append("Agregar JSON-LD con tipos Schema.org relevantes (Article, Organization, FAQPage)")
            elif "Schema.org" in f:
                recs.append("Marcar entidades clave con vocabulario Schema.org")
            elif "Open Graph" in f:
                recs.append("Completar etiquetas Open Graph (og:title, og:description, og:type, og:url)")
            elif "Meta description" in f:
                recs.append("Escribir meta description de 120-160 caracteres con la propuesta de valor")
    recs.extend(d2.get("recommendations", []))
    return recs[:3]


def domain_slug(url):
    parsed = urlparse(url)
    host = (parsed.netloc or parsed.path).replace("www.", "")
    return host.split("/")[0].replace(":", "_") or "sitio"


# ---------- Drawing primitives ----------

def draw_logo(c, x, y, size=18):
    c.setFont("Helvetica-Bold", size)
    c.setFillColor(BLACK)
    c.drawString(x, y, "Visible")
    visible_w = stringWidth("Visible", "Helvetica-Bold", size)
    c.setFillColor(LIME)
    c.drawString(x + visible_w, y, "AI")


def draw_progress_bar(c, x, y, width, height, ratio, fg=LIME, bg=LIGHT_GRAY):
    radius = height / 2
    c.setFillColor(bg)
    c.setStrokeColor(bg)
    c.roundRect(x, y, width, height, radius, stroke=0, fill=1)
    ratio = max(0.0, min(1.0, ratio))
    if ratio > 0:
        fill_w = max(height, width * ratio)
        c.setFillColor(fg)
        c.setStrokeColor(fg)
        c.roundRect(x, y, fill_w, height, radius, stroke=0, fill=1)


def draw_check(c, x, y, size=12):
    c.setFillColor(LIME)
    c.setStrokeColor(LIME)
    c.circle(x + size / 2, y + size / 2, size / 2, stroke=0, fill=1)
    c.setStrokeColor(BLACK)
    c.setLineWidth(1.6)
    p = c.beginPath()
    p.moveTo(x + size * 0.25, y + size * 0.50)
    p.lineTo(x + size * 0.43, y + size * 0.32)
    p.lineTo(x + size * 0.75, y + size * 0.65)
    c.drawPath(p, stroke=1, fill=0)


def draw_cross(c, x, y, size=12):
    c.setFillColor(RED)
    c.setStrokeColor(RED)
    c.circle(x + size / 2, y + size / 2, size / 2, stroke=0, fill=1)
    c.setStrokeColor(WHITE)
    c.setLineWidth(1.6)
    c.line(x + size * 0.30, y + size * 0.30, x + size * 0.70, y + size * 0.70)
    c.line(x + size * 0.30, y + size * 0.70, x + size * 0.70, y + size * 0.30)


def draw_warning(c, x, y, size=12):
    c.setFillColor(AMBER)
    c.setStrokeColor(AMBER)
    c.circle(x + size / 2, y + size / 2, size / 2, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", size * 0.75)
    c.drawCentredString(x + size / 2, y + size * 0.22, "!")


def draw_finding(c, x, y, text, max_width, status="check"):
    icon_size = 13
    text_x = x + icon_size + 10
    text_w = max_width - icon_size - 10
    if status == "check":
        draw_check(c, x, y - 2, icon_size)
    elif status == "cross":
        draw_cross(c, x, y - 2, icon_size)
    elif status == "warn":
        draw_warning(c, x, y - 2, icon_size)
    else:
        c.setFillColor(GRAY)
        c.circle(x + icon_size / 2, y + icon_size / 2 - 2, icon_size / 4, stroke=0, fill=1)
    lines = wrap_text(text, "Helvetica", 10.5, text_w)
    c.setFillColor(BLACK)
    c.setFont("Helvetica", 10.5)
    line_h = 14
    for i, line in enumerate(lines):
        c.drawString(text_x, y - i * line_h, line)
    return max(icon_size, line_h * len(lines)) + 10


def draw_page_footer(c, page_num=None):
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 8)
    c.drawString(MARGIN, MARGIN / 2, "VisibleAI - Reporte AEO")
    if page_num is not None:
        c.drawRightString(PAGE_W - MARGIN, MARGIN / 2, f"{page_num}")


def draw_header_logo(c):
    draw_logo(c, MARGIN, PAGE_H - MARGIN, size=14)
    c.setStrokeColor(LIGHT_GRAY)
    c.setLineWidth(0.8)
    c.line(MARGIN, PAGE_H - MARGIN - 0.5 * cm,
           PAGE_W - MARGIN, PAGE_H - MARGIN - 0.5 * cm)


def draw_section_title(c, title, subtitle, chip_text=None):
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(MARGIN, PAGE_H - MARGIN - 1.8 * cm, title)
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 11)
    c.drawString(MARGIN, PAGE_H - MARGIN - 2.5 * cm, subtitle)
    if chip_text:
        chip_w = 4 * cm
        chip_h = 1.3 * cm
        chip_x = PAGE_W - MARGIN - chip_w
        chip_y = PAGE_H - MARGIN - 2.6 * cm
        c.setFillColor(LIME)
        c.roundRect(chip_x, chip_y, chip_w, chip_h, 0.3 * cm, stroke=0, fill=1)
        c.setFillColor(BLACK)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(chip_x + chip_w / 2, chip_y + 0.4 * cm, chip_text)


# ---------- Pages ----------

def draw_cover(c, url, dt):
    # Bandas decorativas
    c.setFillColor(LIME)
    c.rect(0, PAGE_H - 8 * mm, PAGE_W, 8 * mm, stroke=0, fill=1)
    c.rect(0, 0, PAGE_W, 8 * mm, stroke=0, fill=1)

    # Logo central
    visible_text = "Visible"
    ai_text = "AI"
    visible_w = stringWidth(visible_text, "Helvetica-Bold", 52)
    ai_w = stringWidth(ai_text, "Helvetica-Bold", 52)
    total_w = visible_w + ai_w
    start_x = (PAGE_W - total_w) / 2
    title_y = PAGE_H - 11 * cm
    c.setFont("Helvetica-Bold", 52)
    c.setFillColor(BLACK)
    c.drawString(start_x, title_y, visible_text)
    c.setFillColor(LIME)
    c.drawString(start_x + visible_w, title_y, ai_text)

    # Subtitle
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 14)
    c.drawCentredString(PAGE_W / 2, title_y - 1.1 * cm,
                        "Reporte de Answer Engine Optimization")

    # Linea decorativa
    line_y = title_y - 2.4 * cm
    c.setStrokeColor(LIME)
    c.setLineWidth(3)
    c.line(PAGE_W / 2 - 2 * cm, line_y, PAGE_W / 2 + 2 * cm, line_y)

    # URL
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(PAGE_W / 2, line_y - 1.7 * cm, "Sitio analizado")
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 13)
    display_url = url if len(url) < 70 else url[:67] + "..."
    c.drawCentredString(PAGE_W / 2, line_y - 2.4 * cm, display_url)

    # Fecha
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(PAGE_W / 2, line_y - 3.7 * cm, "Fecha del analisis")
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 13)
    c.drawCentredString(PAGE_W / 2, line_y - 4.4 * cm, format_date_es(dt))

    # Pie de portada
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 9)
    c.drawCentredString(PAGE_W / 2, 1.6 * cm,
                        "visibleai.lat   -   hola@visibleai.lat")


def _draw_dimension_card(c, x, y, w, h, code, title, score, maxv):
    c.setFillColor(LIGHT_GRAY)
    c.setStrokeColor(LIGHT_GRAY)
    c.roundRect(x, y, w, h, 10, stroke=0, fill=1)

    # Badge codigo
    badge_w = 1.2 * cm
    badge_h = 0.7 * cm
    c.setFillColor(LIME)
    c.roundRect(x + 16, y + h - badge_h - 14, badge_w, badge_h, 0.2 * cm,
                stroke=0, fill=1)
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x + 16 + badge_w / 2,
                        y + h - badge_h - 14 + 0.18 * cm, code)

    c.setFillColor(BLACK)
    c.setFont("Helvetica", 10.5)
    c.drawString(x + 16 + badge_w + 10, y + h - badge_h - 14 + 0.18 * cm, title)

    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 36)
    score_str = f"{score}"
    c.drawString(x + 16, y + 32, score_str)
    score_w = stringWidth(score_str, "Helvetica-Bold", 36)
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 14)
    c.drawString(x + 16 + score_w + 6, y + 38, f"/ {maxv}")

    bar_x = x + 16
    bar_w = w - 32
    ratio = score / maxv if maxv else 0
    draw_progress_bar(c, bar_x, y + 14, bar_w, 6, ratio)


def draw_score_page(c, d1, d2):
    draw_header_logo(c)
    total = d1["score"] + d2["score"]
    max_total = d1["max"] + d2["max"]
    pct = total / max_total if max_total else 0

    draw_section_title(c, "Score global",
                       "Puntaje agregado de las dos dimensiones evaluadas.")

    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 96)
    num_y = PAGE_H - MARGIN - 7.5 * cm
    score_str = f"{total}"
    c.drawString(MARGIN, num_y, score_str)
    score_w = stringWidth(score_str, "Helvetica-Bold", 96)
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 24)
    c.drawString(MARGIN + score_w + 8, num_y + 6, f"/ {max_total}")

    # Etiqueta de desempeno
    rating = (
        "Excelente" if pct >= 0.8 else
        "Bueno" if pct >= 0.6 else
        "Aceptable" if pct >= 0.4 else
        "Necesita mejoras"
    )
    c.setFillColor(LIME)
    c.roundRect(PAGE_W - MARGIN - 5 * cm, num_y + 30, 5 * cm, 1.1 * cm,
                0.25 * cm, stroke=0, fill=1)
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(PAGE_W - MARGIN - 2.5 * cm, num_y + 30 + 0.32 * cm,
                        rating)

    # Barra de progreso global
    bar_y = num_y - 1.5 * cm
    draw_progress_bar(c, MARGIN, bar_y, CONTENT_W, 20, pct)
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN, bar_y - 0.8 * cm, f"{pct * 100:.0f}% del puntaje maximo")

    # Tarjetas por dimension
    card_y = bar_y - 6 * cm
    card_w = (CONTENT_W - 1 * cm) / 2
    card_h = 4 * cm
    _draw_dimension_card(c, MARGIN, card_y, card_w, card_h,
                         "D1", "Datos estructurados", d1["score"], d1["max"])
    _draw_dimension_card(c, MARGIN + card_w + 1 * cm, card_y, card_w, card_h,
                         "D2", "Legibilidad semantica", d2["score"], d2["max"])

    draw_page_footer(c, 2)


def draw_d1_page(c, d1, page_num):
    draw_header_logo(c)
    draw_section_title(c, "D1 - Datos estructurados",
                       "JSON-LD, Schema.org, Open Graph y meta description.",
                       chip_text=f"{d1['score']} / {d1['max']}")

    y = PAGE_H - MARGIN - 4.8 * cm
    for finding in d1["findings"]:
        status, text = finding_marker(finding)
        used = draw_finding(c, MARGIN, y, text, CONTENT_W, status)
        y -= used
        if y < MARGIN + 2 * cm:
            break

    draw_page_footer(c, page_num)


def draw_d2_page(c, d2, page_num):
    draw_header_logo(c)
    draw_section_title(c, "D2 - Legibilidad semantica",
                       "Evaluacion con Claude: claridad, autoridad y respuestas directas.",
                       chip_text=f"{d2['score']} / {d2['max']}")

    details = d2.get("details", {}) or {}
    dimensions = [
        ("Claridad", int(details.get("claridad", 0))),
        ("Tono autoritativo", int(details.get("tono_autoritativo", 0))),
        ("Respuestas directas", int(details.get("respuestas_directas", 0))),
    ]
    y = PAGE_H - MARGIN - 4.8 * cm
    for name, value in dimensions:
        c.setFillColor(BLACK)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(MARGIN, y, name)
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 12)
        c.drawRightString(PAGE_W - MARGIN, y, f"{value} / 10")
        draw_progress_bar(c, MARGIN, y - 18, CONTENT_W, 10, value / 10.0)
        y -= 1.5 * cm

    y -= 0.5 * cm
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(MARGIN, y, "Hallazgos cualitativos")
    y -= 0.8 * cm

    findings = d2.get("findings", [])
    # Saltar las 3 primeras lineas (scores numericos ya graficados)
    qualitative = [f for f in findings if not (
        f.startswith("Claridad:") or
        f.startswith("Tono autoritativo:") or
        f.startswith("Respuestas directas:")
    )]
    if not qualitative:
        c.setFillColor(GRAY)
        c.setFont("Helvetica-Oblique", 11)
        c.drawString(MARGIN, y, "Sin hallazgos cualitativos adicionales.")
    else:
        for finding in qualitative:
            status, text = finding_marker(finding)
            if status == "neutral":
                status = "check"
            used = draw_finding(c, MARGIN, y, text, CONTENT_W, status)
            y -= used
            if y < MARGIN + 2 * cm:
                break

    draw_page_footer(c, page_num)


def _draw_recommendation_card(c, x, y, w, n, text):
    text_lines = wrap_text(text, "Helvetica", 11.5, w - 2.6 * cm)
    line_h = 16
    inner_h = max(2.6 * cm, line_h * len(text_lines) + 1.4 * cm)
    bottom = y - inner_h

    c.setFillColor(LIGHT_GRAY)
    c.roundRect(x, bottom, w, inner_h, 12, stroke=0, fill=1)

    # Acento vertical lima izquierdo
    c.setFillColor(LIME)
    c.rect(x, bottom, 5, inner_h, stroke=0, fill=1)

    # Numero
    badge_size = 1.5 * cm
    badge_x = x + 0.6 * cm
    badge_y = y - 0.6 * cm - badge_size
    c.setFillColor(LIME)
    c.roundRect(badge_x, badge_y, badge_size, badge_size, 0.35 * cm,
                stroke=0, fill=1)
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(badge_x + badge_size / 2,
                        badge_y + badge_size / 2 - 8, f"{n}")

    # Texto
    text_x = badge_x + badge_size + 0.7 * cm
    text_y = y - 0.9 * cm
    c.setFillColor(BLACK)
    c.setFont("Helvetica", 11.5)
    for line in text_lines:
        c.drawString(text_x, text_y, line)
        text_y -= line_h

    return inner_h


def draw_recommendations_page(c, recs, page_num):
    draw_header_logo(c)
    draw_section_title(c, "Top 3 recomendaciones",
                       "Acciones priorizadas para mejorar la visibilidad en motores generativos.")

    y = PAGE_H - MARGIN - 4.5 * cm

    if not recs:
        c.setFillColor(GRAY)
        c.setFont("Helvetica-Oblique", 12)
        c.drawString(MARGIN, y,
                     "Excelente trabajo: no hay recomendaciones criticas.")
    else:
        for i, rec in enumerate(recs, 1):
            card_h = _draw_recommendation_card(c, MARGIN, y, CONTENT_W, i, rec)
            y -= card_h + 0.6 * cm

    draw_page_footer(c, page_num)


def draw_closing_page(c):
    # Banda lima superior
    c.setFillColor(LIME)
    c.rect(0, PAGE_H - 8 * mm, PAGE_W, 8 * mm, stroke=0, fill=1)

    # Logo central
    visible_text = "Visible"
    ai_text = "AI"
    visible_w = stringWidth(visible_text, "Helvetica-Bold", 56)
    total_w = visible_w + stringWidth(ai_text, "Helvetica-Bold", 56)
    logo_x = (PAGE_W - total_w) / 2
    logo_y = PAGE_H - 9 * cm
    c.setFont("Helvetica-Bold", 56)
    c.setFillColor(BLACK)
    c.drawString(logo_x, logo_y, visible_text)
    c.setFillColor(LIME)
    c.drawString(logo_x + visible_w, logo_y, ai_text)

    c.setFillColor(GRAY)
    c.setFont("Helvetica", 14)
    c.drawCentredString(PAGE_W / 2, logo_y - 1.3 * cm,
                        "Visibilidad para la era de las respuestas")

    # Separador
    sep_y = logo_y - 2.8 * cm
    c.setStrokeColor(LIME)
    c.setLineWidth(3)
    c.line(PAGE_W / 2 - 2 * cm, sep_y, PAGE_W / 2 + 2 * cm, sep_y)

    # Call to action
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(PAGE_W / 2, sep_y - 2 * cm, "Hablemos.")

    c.setFillColor(GRAY)
    c.setFont("Helvetica", 12)
    c.drawCentredString(PAGE_W / 2, sep_y - 2.8 * cm,
                        "Implementamos las mejoras de este reporte en tu sitio.")

    # Tarjeta de contacto
    card_w = 12 * cm
    card_h = 4 * cm
    card_x = (PAGE_W - card_w) / 2
    card_y = sep_y - 7.5 * cm
    c.setFillColor(BLACK)
    c.roundRect(card_x, card_y, card_w, card_h, 14, stroke=0, fill=1)

    c.setFillColor(GRAY)
    c.setFont("Helvetica", 10.5)
    c.drawCentredString(PAGE_W / 2, card_y + card_h - 1 * cm, "Contacto")

    c.setFillColor(LIME)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(PAGE_W / 2, card_y + card_h - 2.4 * cm,
                        "hola@visibleai.lat")

    c.setFillColor(WHITE)
    c.setFont("Helvetica", 11)
    c.drawCentredString(PAGE_W / 2, card_y + 0.8 * cm, "visibleai.lat")

    # Banda lima inferior
    c.setFillColor(LIME)
    c.rect(0, 0, PAGE_W, 8 * mm, stroke=0, fill=1)

    # Copyright
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 8)
    c.drawCentredString(PAGE_W / 2, 1.3 * cm,
                        f"(c) {datetime.now().year} VisibleAI - Reporte AEO")


# ---------- PDF ----------

def generate_pdf(url, d1, d2, output_path):
    dt = datetime.now()
    c = canvas.Canvas(output_path, pagesize=A4)
    c.setTitle(f"Reporte AEO - {url}")
    c.setAuthor("VisibleAI")
    c.setSubject("Answer Engine Optimization Report")

    draw_cover(c, url, dt)
    c.showPage()

    draw_score_page(c, d1, d2)
    c.showPage()

    draw_d1_page(c, d1, 3)
    c.showPage()

    draw_d2_page(c, d2, 4)
    c.showPage()

    draw_recommendations_page(c, generate_recommendations(d1, d2), 5)
    c.showPage()

    draw_closing_page(c)
    c.showPage()

    c.save()


# ---------- Entry point ----------

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("URL a analizar: ").strip()

    if not url:
        print("Error: URL vacia", file=sys.stderr)
        return 1

    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        print(f"Error: esquema no soportado ({parsed.scheme})", file=sys.stderr)
        return 1

    print(f"Rastreando: {url}")
    try:
        html = fetch_html(url)
    except requests.RequestException as exc:
        print(f"Error al obtener la URL: {exc}", file=sys.stderr)
        return 1

    soup = BeautifulSoup(html, "html.parser")
    print("Analizando D1 (datos estructurados)...")
    d1 = analyze_d1(soup)

    print("Extrayendo texto y analizando D2 con Claude...")
    text = extract_main_text(soup)
    d2 = analyze_d2(text, url)

    fecha = datetime.now().strftime("%Y-%m-%d")
    filename = f"reporte_AEO_{domain_slug(url)}_{fecha}.pdf"
    output = os.path.abspath(filename)

    print(f"Generando PDF: {output}")
    generate_pdf(url, d1, d2, output)
    print(f"PDF generado: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
