# app.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Any, Dict
import base64, os, tempfile, time, asyncio, uuid, json
import httpx
import subprocess
import os
import datetime
import requests
import os
import subprocess
import asyncio
from llm import ask_llm

app = FastAPI(title="Student App Builder Pipeline")

# ---- CONFIG ----
EXPECTED_SECRET = "Jo1010"
EVAL_POST_TIMEOUT_SECONDS = 10 * 60  # 10 minutes

GITHUB_USERNAME = "Shubhankar10"
TASK_NAME = "TDS_try2"
# ----------------

# ---- Pydantic models ----
class Attachment(BaseModel):
    name: str
    url: str  # data URI like data:image/png;base64,....

class RequestPayload(BaseModel):
    email: str
    secret: str
    task: str
    round: int
    nonce: str
    brief: str
    checks: List[str]
    evaluation_url: HttpUrl
    attachments: Optional[List[Attachment]] = Field(default_factory=list)

class AckResponse(BaseModel):
    status: str = "received"
    task: str
    round: int

class EvalResponse(BaseModel):
    """
    {
  // Copy these from the request
  "email": "...",
  "task": "captcha-solver-...",
  "round": 1,
  "nonce": "ab12-...",
  // Send these based on your GitHub repo and commit
  "repo_url": "https://github.com/user/repo",
  "commit_sha": "abc123",
  "pages_url": "https://user.github.io/repo/",
}
    """

# ---- Helper functions ----

def extract_data_uri(data_uri: str):
    """
    Parse data URI of form: data:<mime>;base64,<data>
    returns: (mime, bytes)
    """
    if not data_uri.startswith("data:"):
        raise ValueError("Not a data URI")
    header, b64 = data_uri.split(",", 1)
    # header like: data:image/png;base64
    parts = header.split(";")
    mime = parts[0][5:] if parts[0].startswith("data:") else "application/octet-stream"
    if "base64" not in header:
        raise ValueError("Only base64-encoded data URIs supported")
    return mime, base64.b64decode(b64)

def save_attachments_to_temp(attachments: List[Attachment]) -> List[str]:
    """
    Save attachments to temp files. Return list of file paths.
    """
    saved = []
    for att in attachments:
        mime, data = extract_data_uri(att.url)
        suffix = ""
        if "/" in mime:
            suffix = "." + mime.split("/")[-1]
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tf.write(data)
        tf.flush()
        tf.close()
        saved.append(tf.name)
    return saved

# ---- Github Funcitons ----

def initialize_github(token, username):
    """
    Authenticates GitHub CLI with a personal access token.
    """
    os.environ["GH_TOKEN"] = token
    os.environ["GITHUB_USERNAME"] = username
    # Authenticate GH CLI
    # subprocess.run(["gh", "auth", "login", "--with-token"], input=f"{token}\n", text=True, check=True)
    print("[GITHUB] GitHub CLI authenticated successfully.")

def create_repo(task_name):
    """
    Creates a public GitHub repo with a unique name based on task_name.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    repo_name = f"{task_name}-{timestamp}"
    subprocess.run(["gh", "repo", "create", repo_name, "--public", "--confirm"], check=True)
    print(f"[GITHUB] Repository '{repo_name}' created successfully.")
    return repo_name

def setup_local_repo(repo_name, username,code=""):
    """
    Initializes local git repo, adds MIT LICENSE and README, and pushes code.
    """
    os.makedirs(repo_name, exist_ok=True)
    os.chdir(repo_name)
    print("[GITHUB] Repo Local Made")
    
    # Initialize git
    subprocess.run(["git", "init"], check=True)
    
    # Add MIT LICENSE
    mit_license_text = """MIT License

    Copyright (c) 2025

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction..."""
    with open("LICENSE", "w") as f:
        f.write(mit_license_text)
    
    
    print("[GITHUB] MIT Added")
    # Add README.md
    readme_text = f"""
    # {repo_name}

    ## Summary
    This repository was created programmatically using Python and GitHub CLI.

    """
    
    with open("README.md", "w") as f:
        f.write(readme_text)

    print("[GITHUB] README Added")

    # Add index.html if code is provided
    if code:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(code)
    print("[GITHUB] Code Added.")


    # Commit and push
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit with README and LICENSE"], check=True)
    subprocess.run(["git", "branch", "-M", "main"], check=True)
    subprocess.run(["git", "remote", "add", "origin", f"https://github.com/{username}/{repo_name}.git"], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
    print("[GITHUB] Code pushed successfully.")

def enable_github_pages_api(repo_name, username, token):
    """
    Enable GitHub Pages on the main branch via GitHub API.
    """
    import requests
    import time
    print("[GITHUB] Pages")

    url = f"https://api.github.com/repos/{username}/{repo_name}/pages"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "source": {
            "branch": "main",
            "path": "/"   # Serve from root
        }
    }

    # Try enabling Pages; API may take a moment to process
    response = requests.post(url, json=data, headers=headers)
    
    # If the site already exists, POST returns 422; try PATCH instead
    if response.status_code == 201:
        print(f"GitHub Pages enabled for https://{username}.github.io/{repo_name}/")
    elif response.status_code == 204 or response.status_code == 422:
        # PATCH to update or confirm settings
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code in [200, 201, 204]:
            print(f"GitHub Pages enabled for https://{username}.github.io/{repo_name}/")
        else:
            print(f"Failed to enable GitHub Pages: {response.status_code} {response.text}")
    else:
        print(f"Failed to enable GitHub Pages: {response.status_code} {response.text}")

    # Wait a few seconds for the site to be deployed
    print("[GITHUB] Wait to Publish.")
    time.sleep(10)
    page_url = f"https://{username}.github.io/{repo_name}/"
    print(f"[GITHUB] Check your site at: {page_url}")




def create_github_project(task_name,code):
    token = PERSONAL_ACCESS_TOKEN
    username = GITHUB_USERNAME
    print("Initialize")
    initialize_github(token, username)
    print('Create Repo')
    repo_name = create_repo(task_name)

    print("Setup")
    setup_local_repo(repo_name, username, code=code)

    print('Pages')
    enable_github_pages_api(repo_name, username, token)
    print(f"Project '{repo_name}' setup complete!")

    repo_url = f"https://github.com/{username}/{repo_name}"
    pages_url = f"https://{username}.github.io/{repo_name}/"

    return {"repo_url": repo_url, "commit_sha": "commit_sha", "pages_url": pages_url}

# ---- LLM Functions ----



def post_evaluation_with_retries(evaluation_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post payload (JSON) to evaluation_url using exponential backoff (sync version).
    Keep retrying until either we get HTTP 200 or we surpass EVAL_POST_TIMEOUT_SECONDS.
    Backoff delays: 1,2,4,8... up to 32 sec, but total time must be <= 10 minutes.
    """
    start = time.monotonic()
    attempt = 0
    base_delay = 1.0
    max_delay = 32.0

    with httpx.Client(timeout=30.0) as client:
        while True:
            attempt += 1
            try:
                resp = client.post(
                    evaluation_url, json=payload, headers={"Content-Type": "application/json"}
                )
                if resp.status_code == 200:
                    # success
                    print("[POST] Success")
                    return {"ok": True, "status_code": 200, "text": resp.text}
                else:
                    # non-200 -> retry
                    elapsed = time.monotonic() - start
                    if elapsed >= EVAL_POST_TIMEOUT_SECONDS:
                        print("[POST] Time Out > 10Mins")
                        return {
                            "ok": False,
                            "status_code": resp.status_code,
                            "reason": "timeout exceeded"
                        }
                    delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
                    time.sleep(delay)

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPError) as e:
                elapsed = time.monotonic() - start
                if elapsed >= EVAL_POST_TIMEOUT_SECONDS:
                    print("[POST] Error & Time Out > 10Mins")
                    return {
                        "ok": False,
                        "exception": str(e),
                        "reason": "timeout exceeded"
                    }
                delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
                time.sleep(delay)


# ---- Core background pipeline ----
def pipeline(payload: RequestPayload):
    """
    This function runs asynchronously after immediate 200 ack.
    It:
      - saves attachments,
      - creates repo name,
      - calls create_and_publish_repo_stub (replace with your real function),
      - composes evaluation JSON and posts to evaluation_url with retries.
    """
    
    print(f"[pipeline] started for task={payload.task} round={payload.round}")

    saved_files = []
    try:
        if payload.attachments:
            saved_files = save_attachments_to_temp(payload.attachments)
            print("[pipeline] saved attachments:", saved_files)
    except Exception as e:
        print("[pipeline] failed to save attachments:", e)


    prompt = f"""
    You are an expert web developer. Using the task description {payload.task} and brief {payload.brief}, 
    generate a **single clean code block** that performs this task. 

    - Keep all HTML, CSS, and JavaScript all within <html>..</html>
    - Do not include any introductory or trailing messages, explanations, or comments unrelated to the code.
    - Keep the code simple, readable, and self-contained.
    - Make sure to have these checks in the code : {payload.checks}
    """
    
    # - Use the following attachments as needed: {', '.join(payload.attachments) if payload.attachments else 'None'}.

    import re

    def extract_html_block(code: str) -> str:
        match = re.search(r"(<html.*?>.*?</html>)", code, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1)
        return ""

    # Example usage
    print("[pipeline] Called LLM")
    code = ask_llm(prompt)
    html_only = extract_html_block(code)
    print(html_only)


    # Call LLM here 

    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Sample Page</title>
    </head>
    <body>
        <h1>Hello, GitHub PagesFrom Pipeline!</h1>
        <p>This page was generated automatically.</p>
    </body>
    </html>
    """

    try:
        repo_info = create_github_project(payload.task, html_only)
    except Exception as e:
        print("[pipeline] repo creation failed:", e)
        repo_info = {"repo_url": "", "commit_sha": "", "pages_url": ""}

    eval_payload = {
        "email": payload.email,
        "task": payload.task,
        "round": payload.round,
        "nonce": payload.nonce,
        "repo_url": repo_info.get("repo_url", ""),
        "commit_sha": repo_info.get("commit_sha", ""),
        "pages_url": repo_info.get("pages_url", ""),
    }

# POST 
    print("[pipeline] posting evaluation payload:", eval_payload)
    # result = post_evaluation_with_retries(str(payload.evaluation_url), eval_payload)
    # print("[pipeline] evaluation post result:", result)

    try:
        for p in saved_files:
            os.unlink(p)
    except Exception:
        pass

    print("[pipeline] finished for task:", payload.task)
    return

# ---- FastAPI endpoints ----

@app.post("/api/submit", response_model=AckResponse)
def submit(payload: RequestPayload):

    if payload.secret != EXPECTED_SECRET:
        print("[Submit] Invalid Secret 401")
        raise HTTPException(status_code=401, detail="invalid secret")

    # Immediate ack response
    ack = AckResponse(
        task=payload.task,
        round=payload.round,
    )
    print("[Submit] Repsonse 200")

    pipeline(payload)

    return ack

# ---- If run as main ----
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

    # Send POst to eval url at end 
