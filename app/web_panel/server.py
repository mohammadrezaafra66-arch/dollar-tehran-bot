from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import os

app = FastAPI(title="Afra Automation Platform")


@app.get("/health")
def health():
    path = "data/health.json"

    if not os.path.exists(path):
        return {
            "status": "unknown"
        }

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
    <html>
        <head>
            <title>Afra Automation Platform</title>
        </head>
        <body>
            <h1>Afra Automation Platform</h1>
            <p>Local Control Plane</p>
            <ul>
                <li><a href='/health'>Health</a></li>
            </ul>
        </body>
    </html>
    """
