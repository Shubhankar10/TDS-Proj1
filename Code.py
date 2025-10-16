
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
from llm import initialize_llm_client, ask_llm

import subprocess
import datetime

import os
import base64
from typing import List
import re

from dotenv import load_dotenv  
import os
load_dotenv()

# ---- CONFIG ----
EXPECTED_SECRET = "Jo1010"
EVAL_POST_TIMEOUT_SECONDS = 10 * 60 
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

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

class EvalPayload(BaseModel):
    email: str
    task: str
    round: int
    nonce: str
    repo_url: str
    commit_sha: str
    pages_url: str

# ---- Helper functions ----


def extract_data_uri(data_uri: str) -> tuple[str, bytes]:
    """Extract MIME type and raw bytes from a data URI."""
    header, encoded = data_uri.split(",", 1)
    mime = header.split(";")[0].replace("data:", "")
    data = base64.b64decode(encoded)
    return mime, data

def save_attachments_to_repo(attachments: List) -> List[str]:
    saved_paths = []

    attachments_dir = "attachments"
    os.makedirs(attachments_dir, exist_ok=True)

    for att in attachments:
        # Extract MIME and data
        mime, data = extract_data_uri(att.url)

        # Determine filename and extension
        file_name = att.name
        if "." not in file_name and "/" in mime:
            file_name += "." + mime.split("/")[-1]

        file_path = os.path.join(attachments_dir, file_name)

        with open(file_path, "wb") as f:
            f.write(data)

        saved_paths.append(file_path)

    print(f"[Attachments] Saved {len(saved_paths)} files in {attachments_dir}")
    return saved_paths

def extract_html_block(code: str) -> str:
    match = re.search(r"(<html.*?>.*?</html>)", code, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1)
    return ""

def post_evaluation_with_retries(evaluation_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
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
    return "Posted"


# ---- Github Funcitons ----

def initialize_github(token, username):
    print("[Github : init]")
    os.environ["GH_TOKEN"] = token
    os.environ["GITHUB_USERNAME"] = username
    # Authenticate GH CLI
    # subprocess.run(["gh", "auth", "login", "--with-token"], input=f"{token}\n", text=True, check=True)
    print("[GITHUB : init] GitHub CLI authenticated successfully.")

def create_repo(task_name):
    print("[Github : create repo]")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    repo_name = f"{task_name}-{timestamp}"

    try:
        # Create repo (authenticated via gh auth login)
        subprocess.run(
            ["gh", "repo", "create", repo_name, "--public", "--confirm"],
            check=True
        )

        print(f"[GITHUB : create repo] Repository '{repo_name}' created successfully.")
        return repo_name

    except subprocess.CalledProcessError as e:
        print(f"[pipeline] repo creation failed: {e}")
        raise

def setup_local_repo(repo_name, username,code=""):
    print("[Github : local setup]")
    os.makedirs(repo_name, exist_ok=True)
    os.chdir(repo_name)
    print("[GITHUB : local setup] Repo Local Made")
    
    # Initialize git
    subprocess.run(["git", "init"], check=True)
    
    # Add MIT LICENSE
    mit_license_text = """MIT License

    Copyright (c) 2025

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction."""

    with open("LICENSE", "w") as f:
        f.write(mit_license_text)
    
    
    print("[GITHUB : local setup] MIT Added")
    
    # Commit and push
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit with LICENSE"], check=True)
    subprocess.run(["git", "branch", "-M", "main"], check=True)
    subprocess.run(["git", "remote", "add", "origin", f"https://github.com/{username}/{repo_name}.git"], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
    print("[GITHUB : local setup] Setup successfully.")

def enable_github_pages_api(repo_name, username, token):
    import requests
    import time
    print("[Github] Pages")

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

    return 


# ---- Pipeline Fucnitons ----



def round_2_pipeline(payload: RequestPayload):
    print("Hi")
    return

def round_1_pipeline(payload: RequestPayload):
    print("\n[Round1 Pipeline] Initializing GitHub")
    token = GITHUB_TOKEN
    username = GITHUB_USERNAME
    initialize_github(token, username)

    print("\n[Round1 Pipeline] Creating repository")
    # repo_name = "Talk"
    repo_name = create_repo(payload.task)

    print("\n[Round1 Pipeline] Setup Local repository")
    setup_local_repo(repo_name, username, code="")

    print("\n[Round1 Pipeline] Downloading attachments")
    attachments_paths = save_attachments_to_repo(payload.attachments)

    print("\n[Round1 Pipeline] Calling LLM to generate code with attachments")

    
    
    prompt = f"""
    You are an expert web developer. Using the task description {payload.task} and brief {payload.brief}, 
    generate a **single clean code block** that performs this task. 

    - Keep all HTML, CSS, and JavaScript all within <html>..</html>
    - Do not include any introductory or trailing messages, explanations, or comments unrelated to the code.
    - Keep the code simple, readable, and self-contained.
    - Make sure to have these checks in the code : {payload.checks}
    - Use the following attachments as needed, These are the paths to be used: {attachments_paths}.
    """

    code = ask_llm(prompt)
    html_only = extract_html_block(code)
    # html_only = " "
    print("\t[Round1] Code Generated.")

    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_only)
    print("\t[Round1] Code Added.")



    
    readme_prompt = f"""
    You are an README maker for GITHUB. Using the task description {payload.task} and brief {payload.brief}, 
    generate a **single clean block** that contains the README for this repo : {repo_name}, 
    Here is the code for the task : {html_only}

    - Do not include any introductory or trailing messages, explanations, or comments unrelated to the file.
    - Write a complete README.md under these headings : summary, setup, usage, code explanation.
    """
    
    readme_text = ask_llm(readme_prompt)
    # readme_text = ""
    print("\t[Round1]  README Generated")
    
    with open("README.md", "w") as f:
        f.write(readme_text)

    print("\t[Round1] README Added")


    

    print("\n[Round1 Pipeline] Pushing code to GitHub")
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Add index.html and README for Round1"], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("\t[Round1] Code and Attachments Pushed.")



    print("\n[Round1 Pipeline] Publishing to GitHub Pages")
    enable_github_pages_api(repo_name, username, token)


    print("\n[Round1 Pipeline] Posting results to evaluation URL")

    commit_sha = (
        subprocess.check_output(["git", "rev-parse", "HEAD"])
        .decode("utf-8")
        .strip()
    )

    eval_payload = {
        "email": payload.email,
        "task": payload.task,
        "round": payload.round,
        "nonce": payload.nonce,
    
        "repo_url": f"https://github.com/{username}/{repo_name}",
        "commit_sha": commit_sha,
        "pages_url": f"https://{username}.github.io/{repo_name}/",
    }

    eval_url = "http://127.0.0.2:8000/eval"
    # eval_url = payload.evaluation_url
    
    r = requests.post(eval_url, json=eval_payload)


    print("Status Code:", r.status_code)
    print("Response Text:\n", r.text)

    text = post_evaluation_with_retries(eval_url,eval_payload)
    print(text)

    return
    