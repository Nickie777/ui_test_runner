import os
import subprocess
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from playwright.sync_api import sync_playwright
from pytest_playwright.pytest_playwright import output_path

VIDEO_DIR = "videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/run-test")
def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://playwright.dev/")
        title = page.title()
        browser.close()

    return {"result": title}

@app.get("/record")
def record_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir=VIDEO_DIR
        )
        page = context.new_page()

        page.goto("https://www.google.com/")
        page.get_by_role("link", name="Get started").click()

        context.close()
        browser.close()

    # найдём последний записанный файл
    files = sorted(os.listdir(VIDEO_DIR))
    last_video = files[-1]

    return {"video_file": last_video}

@app.get("/codegen")
def start_codegen():
    output_file = "generated_scenario.py"
    subprocess.Popen(
        [
            "playwright",
            "codegen",
            "https://playwright.dev/",
            "--output",
            output_file
        ]
    )
    return {"status": "Codegen started"}