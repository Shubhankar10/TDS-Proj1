

import requests
import base64

# Example Round 1 payload
payload1 = {
    "email": "student@example.com",
    "secret": "Jo1010",
    "task": "markdown-to-html",
    "round": 1,
    "nonce": "abcd1234",
    "brief": "Publish a static page that converts input.md from attachments to HTML with marked, renders it inside #markdown-output, and loads highlight.js for code blocks.",
    "checks": [
        "js: !!document.querySelector(\"script[src*='marked']\")",
        "js: !!document.querySelector(\"script[src*='highlight.js']\")",
        "js: document.querySelector(\"#markdown-output\").innerHTML.includes(\"<h\")"
    ],
    "evaluation_url": "https://tds-proj1-llm-api.vercel.app/eval",
    "attachments": [
        {"name": "input.md", "url": "data:text/markdown;base64," + base64.b64encode(b"# Hello Markdown").decode()}
    ]
}

# Example Round 2 payload
payload2 = {
    "email": "student@example.com",
    "secret": "Jo1010",
    "task": "markdown-to-html",
    "round": 2,
    "nonce": "abcd1234",
    "brief": "Add tabs #markdown-tabs to switch between rendered HTML and original Markdown, and keep content in sync.",
    "checks": [
        "js: document.querySelectorAll(\"#markdown-tabs button\").length >= 2",
        "js: document.querySelector(\"#markdown-source\").textContent.trim().length > 0"
    ],
    "evaluation_url": "http://127.0.0.2:8000/api/evaluate",
    "attachments": [
        {"name": "input.md", "url": "data:text/markdown;base64," + base64.b64encode(b"# Updated Markdown").decode()}
    ]
}

url = "http://127.0.0.2:8000/api/submit"
# url = "https://tds-proj1-llm-api.vercel.app/api/submit"

# Send Round 1
r1 = requests.post(url, json=payload1)
print("Round 1 Response:")
print(r1.status_code)
# print("Response:", r1.json())

# Send Round 2
r2 = requests.post(url, json=payload2)
print("\nRound 2 Response:")
print(r2.status_code)
# print(r2.status_code, r2.json())
