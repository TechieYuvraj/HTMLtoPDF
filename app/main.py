import os
import io
from typing import Any, Dict

from flask import Flask, jsonify, request, Response, make_response
from flask_cors import CORS
import pdfkit


def create_app() -> Flask:
    app = Flask(__name__)

    # CORS: optional, useful if calling from a browser (n8n server-to-server doesn't require it)
    if os.getenv("ENABLE_CORS", "true").lower() in ("1", "true", "yes"):  # default enabled
        CORS(app)

    # Limit request size (HTML payload). Default ~5MB. Set MAX_HTML_BYTES to override.
    try:
        max_bytes = int(os.getenv("MAX_HTML_BYTES", str(5 * 1024 * 1024)))
    except ValueError:
        max_bytes = 5 * 1024 * 1024
    app.config["MAX_CONTENT_LENGTH"] = max_bytes

    # Try to locate wkhtmltopdf binary (typical paths on Debian/Render Docker)
    wkhtml_path = os.getenv("WKHTMLTOPDF_PATH") or \
        ("/usr/bin/wkhtmltopdf" if os.path.exists("/usr/bin/wkhtmltopdf") else None)
    pdfkit_config = pdfkit.configuration(wkhtmltopdf=wkhtml_path) if wkhtml_path else None

    @app.get("/")
    def index():
        return jsonify({
            "service": "HTML to PDF",
            "status": "ok",
            "endpoints": {
                "health": "/health",
                "convert": "/convert"
            },
            "version": "1.0.0"
        })

    @app.get("/health")
    def health():
        # Basic health endpoint for Render
        return jsonify({"status": "healthy"})

    @app.post("/convert")
    def convert():
        # Expect JSON with { html: string, filename?: string, options?: dict }
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 415

        try:
            payload: Dict[str, Any] = request.get_json(force=True, silent=False)
        except Exception:
            return jsonify({"error": "Invalid JSON"}), 400

        html = payload.get("html")
        if not isinstance(html, str) or not html.strip():
            return jsonify({"error": "Field 'html' (string) is required"}), 400

        # Optional: output filename
        filename = payload.get("filename")
        if not isinstance(filename, str) or not filename.strip():
            filename = "document.pdf"
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        # Optional: wkhtmltopdf options (validated benign subset)
        user_options = payload.get("options", {})
        options: Dict[str, Any] = {
            # Sensible defaults; allow override via user options
            "quiet": None,
            "encoding": "UTF-8",
            "enable-local-file-access": None,
            # Uncomment to harden further if needed:
            # "disable-javascript": None,
        }

        # Whitelist of allowed options to prevent arbitrary flags
        allowed_keys = {
            "page-size", "orientation", "margin-top", "margin-right", "margin-bottom", "margin-left",
            "zoom", "dpi", "encoding", "no-outline", "title", "image-quality", "grayscale",
            "lowquality", "print-media-type", "enable-local-file-access", "disable-javascript",
            "javascript-delay", "viewport-size", "quiet",
        }
        if isinstance(user_options, dict):
            for k, v in user_options.items():
                if k in allowed_keys:
                    options[k] = v

        try:
            pdf_bytes: bytes = pdfkit.from_string(html, False, options=options, configuration=pdfkit_config)
        except OSError as e:
            # Typically wkhtmltopdf not found or rendering error
            return jsonify({"error": "PDF generation failed", "details": str(e)}), 500
        except Exception as e:
            return jsonify({"error": "Unexpected error during PDF generation", "details": str(e)}), 500

        # Stream back the PDF
        resp: Response = make_response(pdf_bytes)
        resp.headers["Content-Type"] = "application/pdf"
        # Hint to treat as attachment; for inline, set to inline
        content_disposition_type = os.getenv("CONTENT_DISPOSITION", "attachment")
        resp.headers["Content-Disposition"] = f"{content_disposition_type}; filename=\"{filename}\""
        resp.headers["Cache-Control"] = "no-store"
        return resp

    return app


app = create_app()
