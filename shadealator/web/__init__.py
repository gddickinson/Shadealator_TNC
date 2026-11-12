"""Web interface for Shade-a-lator TNC (FastAPI + static ES-module front end).

app.py     FastAPI routes under /api and STATIC_ENDPOINTS for the static GitHub Pages export
static/    front end: core.js (router), main.js, pages (home, workflow, demo, results, about), the browser engine
           (scene.js, geometry.js, ttools_engine.js, pipeline.js; tested by pipeline.test.mjs) and static_api.js
"""
