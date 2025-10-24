# HTML to PDF (Python, Render deploy)

A tiny Flask-based web service that converts HTML to PDF using wkhtmltopdf. Designed to be called from n8n via the HTTP Request node (POST JSON) and returns the PDF file in the response.

## Endpoints

- GET `/health` – health check
- POST `/convert` – accepts JSON and returns a PDF

Request body JSON:

```
{
	"html": "<html>...</html>",        // required: HTML string to convert
	"filename": "myfile.pdf",          // optional: output file name (default: document.pdf)
	"options": {                        // optional: wkhtmltopdf options (whitelisted)
		"page-size": "A4",
		"orientation": "Portrait",
		"margin-top": "10mm",
		"margin-right": "10mm",
		"margin-bottom": "10mm",
		"margin-left": "10mm",
		"javascript-delay": 200
	}
}
```

Response: `application/pdf` with `Content-Disposition: attachment; filename="<filename>"`.

## Local Development

Prereqs:

- Docker (recommended) OR wkhtmltopdf installed on your machine

Using Docker (recommended):

```powershell
docker build -t htmltopdf .
docker run --rm -p 8000:8000 htmltopdf
```

Test it:

```powershell
python .\scripts\test_request.py
```

This will save `output.pdf` in the repo root.

## Deploy on Render (Docker)

This repo includes a `Dockerfile` and `render.yaml` (Render Blueprint). To deploy:

1. Push this repository to GitHub/GitLab.
2. On Render, click New + → Blueprint and select the repo containing this project.
3. Confirm settings; Render will detect `render.yaml` and build from `Dockerfile`.
4. After deploy, the service URL will be shown (e.g., `https://html-to-pdf.onrender.com`).

Environment variables in `render.yaml`:

- `ENABLE_CORS` (default true)
- `CONTENT_DISPOSITION` (attachment|inline; default attachment)
- `MAX_HTML_BYTES` (default 5 MB)

## Using from n8n

In your workflow, add an HTTP Request node:

- Method: POST
- URL: `https://<your-render-url>/convert`
- Authentication: None (or add a Header with a secret token if you want to protect it)
- Headers: `Content-Type: application/json`
- Body: Raw, JSON with structure shown above
- Response Format: File

The node output will be the PDF file as binary. You can then use subsequent nodes to store it to Google Drive, S3, etc.

### Example JSON for n8n body

```json
{
	"html": "<!doctype html><html><head><meta charset=\"utf-8\"><title>n8n</title></head><body><h1>Invoice</h1><p>Hello from n8n!</p></body></html>",
	"filename": "invoice.pdf",
	"options": {
		"page-size": "A4",
		"margin-top": "10mm",
		"margin-right": "10mm",
		"margin-bottom": "10mm",
		"margin-left": "10mm"
	}
}
```

Tip for n8n “Using JSON” mode: that input must be valid JSON text. If you use expressions, wrap the whole object with an expression and stringify it, for example:

```
{{ JSON.stringify({
	html: $json.html,
	filename: 'invoice.pdf',
	options: { 'page-size': 'A4', 'margin-top': '10mm', 'margin-right': '10mm', 'margin-bottom': '10mm', 'margin-left': '10mm' }
}) }}
```
Alternatively, choose “Using Fields” and add body parameters (html, filename, options) so n8n builds the JSON for you.

## Security Notes

- Consider adding a simple shared secret via a custom header and reject requests that don’t include it.
- By default, JavaScript is enabled in wkhtmltopdf; if your HTML doesn’t require it, set `options.disable-javascript`.
- The service enforces a max request size; adjust `MAX_HTML_BYTES` to your needs.

## Tech Stack

- Python 3.11, Flask, Gunicorn
- wkhtmltopdf (via pdfkit)

## Troubleshooting

- If you see `wkhtmltopdf not found`, ensure the Docker image is used (or install wkhtmltopdf on your host) or set `WKHTMLTOPDF_PATH` to the correct binary.
- Fonts: the Docker image installs DejaVu fonts. Add more fonts via Dockerfile if needed.

