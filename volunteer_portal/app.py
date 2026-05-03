from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from volunteer_portal.storage import (
    add_feedback,
    create_file_video_record,
    create_prompt_video_record,
    load_records,
)

app = FastAPI(title="Volunteer Dataset Portal")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
    <html>
      <head><title>Volunteer Dataset Portal</title></head>
      <body style="font-family: sans-serif; max-width: 900px; margin: 40px auto;">
        <h1>Volunteer Dataset Portal</h1>
        <p>Current mode: file + final video pairs. Future mode: prompt + video pairs.</p>

        <h2>Submit file + video pair</h2>
        <form action="/submit/file-video" method="post" enctype="multipart/form-data">
          <label>Display name:</label><br/>
          <input type="text" name="display_name"/><br/><br/>
          <label>Project file(s):</label><br/>
          <input type="file" name="project_files" multiple required/><br/><br/>
          <label>Final video:</label><br/>
          <input type="file" name="video" accept="video/*" required/><br/><br/>
          <button type="submit">Submit pair</button>
        </form>

        <h2>Submit prompt + video pair (future extension enabled)</h2>
        <form action="/submit/prompt-video" method="post" enctype="multipart/form-data">
          <label>Display name:</label><br/>
          <input type="text" name="display_name"/><br/><br/>
          <label>Prompt:</label><br/>
          <textarea name="prompt" rows="5" cols="80" required></textarea><br/><br/>
          <label>Video:</label><br/>
          <input type="file" name="video" accept="video/*" required/><br/><br/>
          <button type="submit">Submit prompt/video</button>
        </form>

        <h2>Feedback on an example</h2>
        <form action="/feedback" method="post">
          <label>Example ID:</label><br/>
          <input type="text" name="example_id" required/><br/><br/>
          <label>Author:</label><br/>
          <input type="text" name="author"/><br/><br/>
          <label>Labels (comma-separated):</label><br/>
          <input type="text" name="labels" placeholder="mismatch,artifact,wrong_motion"/><br/><br/>
          <label>Comment:</label><br/>
          <textarea name="comment" rows="4" cols="80" required></textarea><br/><br/>
          <button type="submit">Submit feedback</button>
        </form>

        <h2>Browse records</h2>
        <p><a href="/records">View JSON records</a></p>
      </body>
    </html>
    """


def _persist_temp_upload(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = upload.file.read()
        tmp.write(content)
        return Path(tmp.name)


@app.post("/submit/file-video")
def submit_file_video(
    display_name: str = Form(default=""),
    project_files: list[UploadFile] = File(...),
    video: UploadFile = File(...),
) -> JSONResponse:
    if not project_files:
        raise HTTPException(status_code=400, detail="At least one project file is required")

    temp_project_paths = [_persist_temp_upload(item) for item in project_files]
    temp_video_path = _persist_temp_upload(video)

    record = create_file_video_record(temp_project_paths, temp_video_path, display_name)
    return JSONResponse(record)


@app.post("/submit/prompt-video")
def submit_prompt_video(
    prompt: str = Form(...),
    display_name: str = Form(default=""),
    video: UploadFile = File(...),
) -> JSONResponse:
    temp_video_path = _persist_temp_upload(video)
    record = create_prompt_video_record(prompt=prompt, video_path=temp_video_path, display_name=display_name)
    return JSONResponse(record)


@app.post("/feedback")
def submit_feedback(
    example_id: str = Form(...),
    comment: str = Form(...),
    author: str = Form(default=""),
    labels: str = Form(default=""),
) -> JSONResponse:
    label_list = [item.strip() for item in labels.split(",") if item.strip()]

    try:
        feedback = add_feedback(
            example_id=example_id,
            comment=comment,
            author=author,
            labels=label_list,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return JSONResponse(feedback)


@app.get("/records")
def list_records() -> JSONResponse:
    return JSONResponse(load_records())
