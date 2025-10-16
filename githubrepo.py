#!/usr/bin/env python3
import subprocess
import os
import datetime
import requests

def initialize_github(token, username):
    """
    Authenticates GitHub CLI with a personal access token.
    """
    os.environ["GH_TOKEN"] = token
    os.environ["GITHUB_USERNAME"] = username
    # Authenticate GH CLI
    # subprocess.run(["gh", "auth", "login", "--with-token"], input=f"{token}\n", text=True, check=True)
    print("GitHub CLI authenticated successfully.")

def create_repo(task_name):
    """
    Creates a public GitHub repo with a unique name based on task_name.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    repo_name = f"{task_name}-{timestamp}"
    subprocess.run(["gh", "repo", "create", repo_name, "--public", "--confirm"], check=True)
    print(f"Repository '{repo_name}' created successfully.")
    return repo_name

def setup_local_repo(repo_name, username,code=""):
    """
    Initializes local git repo, adds MIT LICENSE and README, and pushes code.
    """
    os.makedirs(repo_name, exist_ok=True)
    os.chdir(repo_name)
    
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
    
    # Add README.md
    readme_text = f"""
    # {repo_name}

    ## Summary
    This repository was created programmatically using Python and GitHub CLI.

    """
    
    with open("README.md", "w") as f:
        f.write(readme_text)

    # Add index.html if code is provided
    if code:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(code)


    # Commit and push
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit with README and LICENSE"], check=True)
    subprocess.run(["git", "branch", "-M", "main"], check=True)
    subprocess.run(["git", "remote", "add", "origin", f"https://github.com/{username}/{repo_name}.git"], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
    print("Code pushed successfully.")

def enable_github_pages_api(repo_name, username, token):
    """
    Enable GitHub Pages on the main branch via GitHub API.
    """
    import requests
    import time

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
    time.sleep(5)
    page_url = f"https://{username}.github.io/{repo_name}/"
    print(f"Check your site at: {page_url}")

def create_github_project(task_name, token, username):
    print('1')
    initialize_github(token, username)
    print('2')
    repo_name = create_repo(task_name)
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Sample Page</title>
    </head>
    <body>
        <h1>Hello, GitHub Pages!</h1>
        <p>This page was generated automatically.</p>
    </body>
    </html>
    """

    setup_local_repo(repo_name, username, code=html_code)

    print('3')
    enable_github_pages_api(repo_name, username, token)
    print(f"Project '{repo_name}' setup complete!")


PERSONAL_ACCESS_TOKEN = ""
GITHUB_USERNAME = "Shubhankar10"
TASK_NAME = "TDS_try2"
create_github_project(TASK_NAME, PERSONAL_ACCESS_TOKEN, GITHUB_USERNAME)

#Code to push main as well

