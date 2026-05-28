#!/usr/bin/env python3
"""API Flask para VisibleAI: analiza una URL y devuelve un reporte AEO en PDF."""

import os
import tempfile
import traceback
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from crawler import analyze_d1, analyze_d2, extract_main_text, fetch_html
from generar_reporte import domain_slug, generate_pdf

app = Flask(__name__)
CORS(app)


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Endpoint no encontrado"}), 404


@app.errorhandler(405)
def method_not_allowed(_error):
    return jsonify({"error": "Metodo no permitido para este endpoint"}), 405


@app.errorhandler(500)
def server_error(_error):
    return jsonify({"error": "Error interno del servidor"}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/analizar", methods=["POST"])
def analizar():
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400

    payload = request.get_json(silent=True) or {}
    url = (payload.get("url") or "").strip()

    if not url:
        return jsonify({"error": "El campo 'url' es obligatorio"}), 400

    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return jsonify({"error": f"Esquema no soportado: {parsed.scheme}"}), 400

    if not parsed.netloc:
        return jsonify({"error": "URL invalida"}), 400

    try:
        html = fetch_html(url)
    except requests.RequestException as exc:
        return jsonify({"error": f"No se pudo obtener la URL: {exc}"}), 502

    try:
        soup = BeautifulSoup(html, "html.parser")
        d1 = analyze_d1(soup)
        text = extract_main_text(soup)
        d2 = analyze_d2(text, url)
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": f"Error al analizar la URL: {exc}"}), 500

    fecha = datetime.now().strftime("%Y-%m-%d")
    filename = f"reporte_AEO_{domain_slug(url)}_{fecha}.pdf"

    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.close()
        generate_pdf(url, d1, d2, tmp.name)
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": f"Error al generar el PDF: {exc}"}), 500

    response = send_file(
        tmp.name,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )

    @response.call_on_close
    def _cleanup():
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
