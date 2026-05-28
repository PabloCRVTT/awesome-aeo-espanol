#!/usr/bin/env python3
"""Crawler AEO para VisibleAI.

Analiza una URL en dos dimensiones:
  D1 (20 pts) - Datos estructurados: JSON-LD, Schema.org, Open Graph, meta description
  D2 (30 pts) - Legibilidad semantica: claridad, tono autoritativo, respuestas directas
"""

import json
import os
import sys
from urllib.parse import urlparse

import anthropic
import requests
from bs4 import BeautifulSoup

MODEL = "claude-sonnet-4-6"
MAX_TEXT_CHARS = 12000


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; VisibleAI-AEO-Crawler/1.0; "
            "+https://visibleai.com/crawler)"
        )
    }
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response.text


def analyze_d1(soup: BeautifulSoup) -> dict:
    """D1 - Datos estructurados (20 pts)."""
    findings: list[str] = []
    score = 0

    # JSON-LD (8 pts)
    jsonld_scripts = soup.find_all("script", type="application/ld+json")
    valid_jsonld: list[dict] = []
    for script in jsonld_scripts:
        try:
            data = json.loads(script.string or "")
            valid_jsonld.append(data)
        except (json.JSONDecodeError, TypeError):
            continue

    if valid_jsonld:
        score += 8
        findings.append(f"OK JSON-LD encontrado ({len(valid_jsonld)} bloque(s))")
    else:
        findings.append("FALTA JSON-LD no encontrado")

    # Schema.org types (4 pts)
    schema_types: set[str] = set()
    for block in valid_jsonld:
        items = block if isinstance(block, list) else [block]
        for item in items:
            if isinstance(item, dict) and "@type" in item:
                t = item["@type"]
                if isinstance(t, list):
                    schema_types.update(t)
                else:
                    schema_types.add(t)

    microdata = soup.find_all(attrs={"itemtype": True})
    if microdata:
        for tag in microdata:
            itemtype = tag.get("itemtype", "")
            if "schema.org" in itemtype:
                schema_types.add(itemtype.rsplit("/", 1)[-1])

    if schema_types:
        score += 4
        findings.append(f"OK Schema.org types: {', '.join(sorted(schema_types))}")
    else:
        findings.append("FALTA Schema.org no detectado")

    # Open Graph (4 pts)
    og_tags = soup.find_all("meta", property=lambda x: x and x.startswith("og:"))
    og_props = {tag.get("property"): tag.get("content", "") for tag in og_tags}
    required_og = {"og:title", "og:description", "og:type", "og:url"}
    present_og = required_og & set(og_props.keys())

    if len(present_og) >= 3:
        score += 4
        findings.append(f"OK Open Graph completo ({len(og_tags)} etiquetas)")
    elif og_tags:
        score += 2
        findings.append(f"PARCIAL Open Graph parcial ({len(og_tags)} etiquetas, faltan: {required_og - present_og})")
    else:
        findings.append("FALTA Open Graph ausente")

    # Meta description (4 pts)
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        content = meta_desc["content"].strip()
        length = len(content)
        if 120 <= length <= 160:
            score += 4
            findings.append(f"OK Meta description optima ({length} chars)")
        elif 50 <= length < 120 or 160 < length <= 200:
            score += 2
            findings.append(f"PARCIAL Meta description subobtima ({length} chars)")
        else:
            score += 1
            findings.append(f"PARCIAL Meta description fuera de rango ({length} chars)")
    else:
        findings.append("FALTA Meta description ausente")

    return {
        "score": score,
        "max": 20,
        "findings": findings,
        "details": {
            "jsonld_count": len(valid_jsonld),
            "schema_types": sorted(schema_types),
            "og_tags": list(og_props.keys()),
            "meta_description": meta_desc.get("content", "") if meta_desc else "",
        },
    }


def extract_main_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.body
    if main is None:
        return ""

    text = main.get_text(separator=" ", strip=True)
    return " ".join(text.split())


def analyze_d2(text: str, url: str) -> dict:
    """D2 - Legibilidad semantica via Claude (30 pts)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "score": 0,
            "max": 30,
            "findings": ["ERROR ANTHROPIC_API_KEY no configurada"],
            "recommendations": [],
        }

    if not text.strip():
        return {
            "score": 0,
            "max": 30,
            "findings": ["ERROR No se pudo extraer texto principal"],
            "recommendations": [],
        }

    snippet = text[:MAX_TEXT_CHARS]
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Eres un auditor AEO (Answer Engine Optimization) que evalua contenido web para que motores de busqueda generativos (ChatGPT, Perplexity, Claude) lo citen como fuente autoritativa.

URL analizada: {url}

Texto principal extraido:
\"\"\"
{snippet}
\"\"\"

Evalua tres dimensiones (0-10 cada una):

1. CLARIDAD (0-10): El contenido es facilmente comprensible? Frases cortas, terminologia consistente, estructura logica.
2. TONO_AUTORITATIVO (0-10): Demuestra expertise? Cita datos, fuentes, ejemplos concretos. Evita hedging excesivo.
3. RESPUESTAS_DIRECTAS (0-10): Responde preguntas explicitamente? Hay parrafos auto-contenidos que un LLM podria citar como respuesta?

Devuelve SOLO un JSON valido con esta estructura exacta:
{{
  "claridad": <int 0-10>,
  "tono_autoritativo": <int 0-10>,
  "respuestas_directas": <int 0-10>,
  "hallazgos": ["<hallazgo 1>", "<hallazgo 2>", "<hallazgo 3>"],
  "recomendaciones": ["<recomendacion 1>", "<recomendacion 2>", "<recomendacion 3>"]
}}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = next((b.text for b in message.content if b.type == "text"), "")
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "score": 0,
            "max": 30,
            "findings": [f"ERROR Respuesta de Claude no parseable: {raw[:200]}"],
            "recommendations": [],
        }

    claridad = int(data.get("claridad", 0))
    tono = int(data.get("tono_autoritativo", 0))
    respuestas = int(data.get("respuestas_directas", 0))
    score = claridad + tono + respuestas

    findings = [
        f"Claridad: {claridad}/10",
        f"Tono autoritativo: {tono}/10",
        f"Respuestas directas: {respuestas}/10",
    ] + list(data.get("hallazgos", []))

    return {
        "score": score,
        "max": 30,
        "findings": findings,
        "recommendations": list(data.get("recomendaciones", [])),
        "details": {
            "claridad": claridad,
            "tono_autoritativo": tono,
            "respuestas_directas": respuestas,
        },
    }


def print_report(url: str, d1: dict, d2: dict) -> None:
    total = d1["score"] + d2["score"]
    max_total = d1["max"] + d2["max"]

    print()
    print("=" * 70)
    print(f"  REPORTE AEO - VisibleAI")
    print(f"  URL: {url}")
    print("=" * 70)
    print()
    print(f"SCORE PARCIAL: {total}/{max_total}")
    print(f"  D1 (Datos estructurados):  {d1['score']}/{d1['max']}")
    print(f"  D2 (Legibilidad semantica): {d2['score']}/{d2['max']}")
    print()
    print("-" * 70)
    print("D1 - HALLAZGOS")
    print("-" * 70)
    for f in d1["findings"]:
        print(f"  {f}")
    print()
    print("-" * 70)
    print("D2 - HALLAZGOS")
    print("-" * 70)
    for f in d2["findings"]:
        print(f"  {f}")
    print()
    print("-" * 70)
    print("TOP 3 RECOMENDACIONES")
    print("-" * 70)

    recommendations: list[str] = []
    for f in d1["findings"]:
        if f.startswith("FALTA") or f.startswith("PARCIAL"):
            if "JSON-LD" in f:
                recommendations.append("Agregar JSON-LD con tipos Schema.org relevantes (Article, Organization, FAQPage)")
            elif "Schema.org" in f:
                recommendations.append("Marcar entidades clave con vocabulario Schema.org")
            elif "Open Graph" in f:
                recommendations.append("Completar etiquetas Open Graph (og:title, og:description, og:type, og:url)")
            elif "Meta description" in f:
                recommendations.append("Escribir meta description de 120-160 caracteres con la propuesta de valor")

    recommendations.extend(d2.get("recommendations", []))

    for i, rec in enumerate(recommendations[:3], 1):
        print(f"  {i}. {rec}")

    if not recommendations:
        print("  (No hay recomendaciones criticas - excelente trabajo)")
    print()
    print("=" * 70)
    print()


def main() -> int:
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

    print_report(url, d1, d2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
