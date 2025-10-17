
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

import requests
import base64
from datetime import datetime

from dotenv import load_dotenv  
import os
load_dotenv()

# ---- CONFIG ----
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

# def save_attachments_to_repo(attachments: List) -> List[str]:
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


def prepare_attachments_for_push(attachments: List) -> dict:
    """
    Prepare attachments as a dictionary for push_code function.
    Returns dict with file paths as keys and file contents as values.
    """
    files_dict = {}
    
    for att in attachments:
        # Extract MIME and data
        mime, data = extract_data_uri(att.url)

        # Determine filename and extension
        file_name = att.name
        if "." not in file_name and "/" in mime:
            file_name += "." + mime.split("/")[-1]

        # Add to files dict with attachments/ prefix
        file_path = f"attachments/{file_name}"
        files_dict[file_path] = data

    print(f"[Attachments] Prepared {len(files_dict)} files for push")
    return files_dict

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

# def create_repo(task_name):
#     print("[Github : create repo]")
#     timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
#     print("[Test] Timestamp Issue")
#     repo_name = f"{task_name}-{timestamp}"

#     try:
#         # Create repo (authenticated via gh auth login)
#         subprocess.run(
#             ["gh", "repo", "create", repo_name, "--public", "--confirm"],
#             check=True
#         )
#         print("[Test] Suprocess Issue")

#         print(f"[GITHUB : create repo] Repository '{repo_name}' created successfully.")
#         return repo_name

#     except subprocess.CalledProcessError as e:
#         print(f"[pipeline] repo creation failed: {e}")
#         raise


# def setup_local_repo(repo_name, username):
#     print("[Github : local setup]")
#     os.makedirs(repo_name, exist_ok=True)
#     os.chdir(repo_name)
#     print("[GITHUB : local setup] Repo Local Made")
    
#     # Initialize git
#     subprocess.run(["git", "init"], check=True)
    
#     # Add MIT LICENSE
#     mit_license_text = """MIT License

#     Copyright (c) 2025

#     Permission is hereby granted, free of charge, to any person obtaining a copy
#     of this software and associated documentation files (the "Software"), to deal
#     in the Software without restriction."""

#     with open("LICENSE", "w") as f:
#         f.write(mit_license_text)
    
    
#     print("[GITHUB : local setup] MIT Added")
    
#     # Commit and push
#     subprocess.run(["git", "add", "."], check=True)
#     subprocess.run(["git", "commit", "-m", "Initial commit with LICENSE"], check=True)
#     subprocess.run(["git", "branch", "-M", "main"], check=True)
#     subprocess.run(["git", "remote", "add", "origin", f"https://github.com/{username}/{repo_name}.git"], check=True)
#     subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
#     print("[GITHUB : local setup] Setup successfully.")

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



# claude


def create_repo(task_name, github_token):
    print("[Github : create repo]")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    print("[Test] Timestamp Issue")
    repo_name = f"{task_name}-{timestamp}"

    try:
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        data = {
            "name": repo_name,
            "private": False,
            "auto_init": False
        }
        
        response = requests.post(
            "https://api.github.com/user/repos",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        
        print("[Test] Suprocess Issue")
        print(f"[GITHUB : create repo] Repository '{repo_name}' created successfully.")
        return repo_name

    except requests.exceptions.RequestException as e:
        print(f"[pipeline] repo creation failed: {e}")
        raise


def setup_local_repo(repo_name, username, github_token):
    print("[Github : local setup]")
    
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    print("[GITHUB : local setup] Repo Local Made")
    
    # Add MIT LICENSE via API
    mit_license_text = """MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction."""

    content_encoded = base64.b64encode(mit_license_text.encode()).decode()
    
    data = {
        "message": "Initial commit with LICENSE",
        "content": content_encoded,
        "branch": "main"
    }
    
    response = requests.put(
        f"https://api.github.com/repos/{username}/{repo_name}/contents/LICENSE",
        headers=headers,
        json=data
    )
    response.raise_for_status()
    
    print("[GITHUB : local setup] MIT Added")
    print("[GITHUB : local setup] Setup successfully.")


def push_code(repo_name, username, github_token, files_dict, commit_message="Add index.html and README for Round1"):
    """
    Push multiple files to GitHub repo in a single commit using Git Database API.
    
    Args:
        repo_name: Name of the repository
        username: GitHub username
        github_token: GitHub personal access token
        files_dict: Dictionary where keys are file paths and values are file contents (as strings or bytes)
                   Example: {"index.html": "<html>...</html>", "README.md": "# Title"}
        commit_message: Commit message
    """
    print("\n[Round1 Pipeline] Pushing code to GitHub")
    
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    try:
        # Get the current commit SHA of the main branch
        ref_response = requests.get(
            f"https://api.github.com/repos/{username}/{repo_name}/git/ref/heads/main",
            headers=headers
        )
        ref_response.raise_for_status()
        current_commit_sha = ref_response.json()["object"]["sha"]
        
        # Get the tree SHA of the current commit
        commit_response = requests.get(
            f"https://api.github.com/repos/{username}/{repo_name}/git/commits/{current_commit_sha}",
            headers=headers
        )
        commit_response.raise_for_status()
        base_tree_sha = commit_response.json()["tree"]["sha"]
        
        # Create blobs for all files
        tree_items = []
        for file_path, file_content in files_dict.items():
            # Convert content to bytes if it's a string
            if isinstance(file_content, str):
                file_content = file_content.encode('utf-8')
            
            # Encode content to base64
            content_base64 = base64.b64encode(file_content).decode()
            
            # Create blob
            blob_data = {
                "content": content_base64,
                "encoding": "base64"
            }
            
            blob_response = requests.post(
                f"https://api.github.com/repos/{username}/{repo_name}/git/blobs",
                headers=headers,
                json=blob_data
            )
            blob_response.raise_for_status()
            blob_sha = blob_response.json()["sha"]
            
            # Add to tree
            tree_items.append({
                "path": file_path,
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha
            })
        
        # Create new tree
        tree_data = {
            "base_tree": base_tree_sha,
            "tree": tree_items
        }
        
        tree_response = requests.post(
            f"https://api.github.com/repos/{username}/{repo_name}/git/trees",
            headers=headers,
            json=tree_data
        )
        tree_response.raise_for_status()
        new_tree_sha = tree_response.json()["sha"]
        
        # Create new commit
        commit_data = {
            "message": commit_message,
            "tree": new_tree_sha,
            "parents": [current_commit_sha]
        }
        
        new_commit_response = requests.post(
            f"https://api.github.com/repos/{username}/{repo_name}/git/commits",
            headers=headers,
            json=commit_data
        )
        new_commit_response.raise_for_status()
        new_commit_sha = new_commit_response.json()["sha"]
        
        # Update the reference
        update_ref_data = {
            "sha": new_commit_sha,
            "force": False
        }
        
        update_ref_response = requests.patch(
            f"https://api.github.com/repos/{username}/{repo_name}/git/refs/heads/main",
            headers=headers,
            json=update_ref_data
        )
        update_ref_response.raise_for_status()
        
        print("\t[Round1] Code and Attachments Pushed.")
        
    except requests.exceptions.RequestException as e:
        print(f"[pipeline] push code failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        raise



# ---- Pipeline Fucnitons ----


def round_2_pipeline(payload : RequestPayload,round1_data: dict):
    print("\n [Round 2]")
    repo_name = round1_data["repo_name"]
    files = round1_data["files"]
    attachments = round1_data["attachments"]
    commit_sha = round1_data["commit_sha"]
    repo_url = round1_data["repo_url"]
    pages_url = round1_data["pages_url"]
    round1_task = round1_data["task"]
    token = GITHUB_TOKEN
    username = GITHUB_USERNAME

    
    prompt_round2_code = f"""
    You are an expert web developer. Using the task '{payload.task}' and brief '{payload.brief}', 
    generate a **complete, standalone HTML page** that implements the updated functionality. 

    - Include all HTML, CSS, and JavaScript within <html>..</html>.
    - Use attachments if needed: {attachments}.
    - Ensure the code passes these checks: {payload.checks}. Do not add checks on HTML, just confirm them yourself.
    - Keep it clean, simple, and fully self-contained.
    """
    code = ask_llm(prompt_round2_code)
    html_only = extract_html_block(code)
    # html_only = " "
    print("\t[Round2] Code Generated.")
    files["index.html"] = html_only

    print("\t[Round2] Code Added.")



    
    # Prompt for generating updated README.md for Round 2
    prompt_round2_readme = f"""
    You are a README generator for GitHub. Based on task '{payload.task}' and brief '{payload.brief}', 
    write a **complete README.md** that replaces the Round 1 README entirely. 

    - Include sections: summary, setup, usage, code explanation.
    - Do not include extra messages or unrelated comments.
    - Generate a response fast and accurate.
    - Reference the new code generated for Round 2 : {html_only}.
    """
    
    readme_text = ask_llm(prompt_round2_readme)
    match = re.search(r'(^#.*?)(?=\n[^#]|$)', readme_text, re.DOTALL | re.MULTILINE)
    if match:
        readme_text = match.group(0)
    
    # readme_text = ""
    print("\t[Round2]  README Generated")
    files["README.md"] = readme_text

    print("\t[Round2] README Added")


    

    print("\n[Round2 Pipeline] Pushing code to GitHub")
    push_code(repo_name, username, token, files, "Round 2 : Added index.html, README and attachments")
        
    print("\t[Round2] Code and Attachments Pushed.")



    # POST 
    
    commit_sha2 = requests.get(f"https://api.github.com/repos/{username}/{repo_name}/git/refs/heads/main", headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}).json()["object"]["sha"]

    
    eval_payload = {
        "email": payload.email,
        "task": payload.task,
        "round": payload.round,
        "nonce": payload.nonce,
    
        "repo_url": repo_url,
        "commit_sha": commit_sha2,
        "pages_url": pages_url,
    }


    # eval_url = "http://127.0.0.2:8000/eval"
    eval_url = payload.evaluation_url
    
    # r = requests.post(eval_url, json=eval_payload)


    # print("Status Code:", r.status_code)
    # print("Response Text:\n", r.text)

    text = post_evaluation_with_retries(eval_url,eval_payload)
    print(text)

    print("[Round2] Done.")
    return




def round_1_pipeline(payload: RequestPayload):
    print("\n[Round1 Pipeline] Initializing GitHub")
    token = GITHUB_TOKEN
    username = GITHUB_USERNAME
    initialize_github(token, username)

    print("\n[Round1 Pipeline] Creating repository")
    # repo_name = "Talk"
    repo_name = create_repo(payload.task,token)

    print("\n[Round1 Pipeline] Setup Local repository")
    setup_local_repo(repo_name,username, token)

    print("\n[Round1 Pipeline] Downloading attachments")

    files = {}

    if payload.attachments:
        attachment_files = prepare_attachments_for_push(payload.attachments)
        files.update(attachment_files) 

    print("\n[Round1 Pipeline] Calling LLM to generate code with attachments")

    
    
    prompt = f"""
    You are an expert web developer. Using the task description {payload.task} and brief {payload.brief}, 
    generate a **single clean code block** that performs this task. 

    - Keep all HTML, CSS, and JavaScript all within <html>..</html>
    - Do not include any introductory or trailing messages, explanations, or comments unrelated to the code.
    - Keep the code simple, readable, and self-contained.
    - Make sure to have these checks in the code : {payload.checks}
    - Use the following attachments as needed, These are the paths to be used: {attachment_files}.
    """

    code = ask_llm(prompt)
    html_only = extract_html_block(code)
    # html_only = " "
    print("\t[Round1] Code Generated.")

    
    # with open("index.html", "w", encoding="utf-8") as f:
    #     f.write(html_only)
    files["index.html"] = html_only

    print("\t[Round1] Code Added.")



    
    readme_prompt = f"""
    You are an README maker for GITHUB. Using the task description {payload.task} and brief {payload.brief}, 
    generate a **single clean block** that contains the README for this repo : {repo_name}, 
    Here is the code for the task : {html_only}

    - Do not include any introductory or trailing messages, explanations, or comments unrelated to the file.
    - Write a complete README.md under these headings : summary, setup, usage, code explanation.
    - Generate a response fast and accurate
    """
    
    readme_text = ask_llm(readme_prompt)
    match = re.search(r'(^#.*?)(?=\n[^#]|$)', readme_text, re.DOTALL | re.MULTILINE)
    if match:
        readme_text = match.group(0)
    
    # readme_text = ""
    print("\t[Round1]  README Generated")
    
    # with open("README.md", "w") as f:
    #     f.write(readme_text)
    files["README.md"] = readme_text

    print("\t[Round1] README Added")


    

    print("\n[Round1 Pipeline] Pushing code to GitHub")
    # subprocess.run(["git", "add", "."], check=True)
    # subprocess.run(["git", "commit", "-m", "Add index.html and README for Round1"], check=True)
    # subprocess.run(["git", "push", "origin", "main"], check=True)

    # Create files in memory (no file system needed)

    push_code(repo_name, username, token, files, "Added index.html, README and attachments")
        
    print("\t[Round1] Code and Attachments Pushed.")



    print("\n[Round1 Pipeline] Publishing to GitHub Pages")
    enable_github_pages_api(repo_name, username, token)


    print("\n[Round1 Pipeline] Posting results to evaluation URL")
    time.sleep(10)

    commit_sha = requests.get(f"https://api.github.com/repos/{username}/{repo_name}/git/refs/heads/main", headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}).json()["object"]["sha"]

    print(f"[Round 1] SHA : {commit_sha}")
    eval_payload = {
        "email": payload.email,
        "task": payload.task,
        "round": payload.round,
        "nonce": payload.nonce,
    
        "repo_url": f"https://github.com/{username}/{repo_name}",
        "commit_sha": commit_sha,
        "pages_url": f"https://{username}.github.io/{repo_name}/",
    }


    # eval_url = "http://127.0.0.2:8000/eval"
    eval_url = payload.evaluation_url
    
    # r = requests.post(eval_url, json=eval_payload)


    # print("Status Code:", r.status_code)
    # print("Response Text:\n", r.text)

    text = post_evaluation_with_retries(eval_url,eval_payload)
    print(text)

    # At the end of round_1_pipeline:
    return {
        "repo_name": repo_name,
        "files": files,
        "attachments": attachment_files if payload.attachments else {},
        "commit_sha": commit_sha,
        "repo_url": f"https://github.com/{username}/{repo_name}",
        "pages_url": f"https://{username}.github.io/{repo_name}/",
        "task": payload.task,
    }

    