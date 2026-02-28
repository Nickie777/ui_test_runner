import os
import subprocess
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from playwright.sync_api import sync_playwright
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
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

@app.get("/run-generated")
def run_generated():
    file_to_run = "generated_scenario.py"

    if not os.path.exists(file_to_run):
        return {"error": "File not found"}

    # Запускаем код в отдельном процессе
    result = subprocess.run(
        ["python", file_to_run],
        capture_output=True, text=True
    )

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }

@app.websocket("/ws/run-generated")
async def websocket_run_generated(ws: WebSocket, GENERATED_FILE="generated_scenario.py"):
    await ws.accept()

    if not os.path.exists(GENERATED_FILE):
        await ws.send_text("Error: generated_scenario.py not found")
        await ws.close()
        return

    # Запуск скрипта как subprocess
    process = subprocess.Popen(
        ["python", GENERATED_FILE],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    try:
        # Чтение stdout по строчно и отправка в вебсокет
        while True:
            line = process.stdout.readline()
            if line:
                await ws.send_text(line.strip())
            elif process.poll() is not None:
                break

        # Дошли до конца
        await ws.send_text(f"Process finished with return code {process.returncode}")
    except WebSocketDisconnect:
        process.kill()