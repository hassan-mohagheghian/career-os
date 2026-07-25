"""Live API documentation — Swagger UI and ReDoc."""

import json
import os

from flask import Blueprint, Response

bp = Blueprint('api_docs', __name__)

_docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'api-docs')


@bp.route('/api/swagger.json')
def swagger_json():
    """Serve the OpenAPI 3.0 spec as JSON."""
    spec_path = os.path.join(_docs_dir, 'openapi.json')
    with open(spec_path) as f:
        spec = json.load(f)
    return Response(json.dumps(spec, indent=2), mimetype='application/json')


@bp.route('/api/docs/')
def swagger_ui():
    """Swagger UI — interactive API explorer."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>API Docs — Swagger UI</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
  <style>body { margin: 0; padding: 0; }</style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
  <script>
    SwaggerUIBundle({
      url: '/api/swagger.json',
      dom_id: '#swagger-ui',
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
      layout: 'StandaloneLayout',
    });
  </script>
</body>
</html>"""


@bp.route('/api/redoc')
def redoc():
    """ReDoc — alternative API documentation viewer."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>API Docs — ReDoc</title>
  <link rel="stylesheet" href="https://unpkg.com/redoc@2/bundles/redoc.standalone.css">
</head>
<body>
  <redoc spec-url='/api/swagger.json'></redoc>
  <script src="https://unpkg.com/redoc@2/bundles/redoc.standalone.js"></script>
</body>
</html>"""
