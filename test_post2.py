import requests
import base64
import time
# # Example Round 1 payload
# payload1 = {
#     "email": "student@example.com",
#     "secret": "Jo1010",
#     "task": "markdown-to-html",
#     "round": 1,
#     "nonce": "abcd1234",
#     "brief": "Publish a static page that converts input.md from attachments to HTML with marked, renders it inside #markdown-output, and loads highlight.js for code blocks.",
#     "checks": [
#         "js: !!document.querySelector(\"script[src*='marked']\")",
#         "js: !!document.querySelector(\"script[src*='highlight.js']\")",
#         "js: document.querySelector(\"#markdown-output\").innerHTML.includes(\"<h\")"
#     ],
#     "evaluation_url": "https://tds-proj1-llm-api.vercel.app/eval",
#     "attachments": [
#         {"name": "input.md", "url": "data:text/markdown;base64," + base64.b64encode(b"# Hello Markdown").decode()}
#     ]
# }

# # Example Round 2 payload
# payload2 = {
#     "email": "student@example.com",
#     "secret": "Jo1010",
#     "task": "markdown-to-html",
#     "round": 2,
#     "nonce": "abcd1234",
#     "brief": "Add tabs #markdown-tabs to switch between rendered HTML and original Markdown, and keep content in sync.",
#     "checks": [
#         "js: document.querySelectorAll(\"#markdown-tabs button\").length >= 2",
#         "js: document.querySelector(\"#markdown-source\").textContent.trim().length > 0"
#     ],
#     "evaluation_url": "http://127.0.0.2:8000/api/evaluate",
#     "attachments": [
#         {"name": "input.md", "url": "data:text/markdown;base64," + base64.b64encode(b"# Updated Markdown").decode()}
#     ]
# }

import base64

# Round 1 payload
payload1 = {
    "email": "student@example.com",
    "secret": "Jo1010",
    "task": "sum-of-sales",
    "round": 1,
    "nonce": "abcd1234",
    "brief": "Publish a single-page site that fetches data.csv from attachments, sums its sales column, sets the title to \"Sales Summary ${seed}\", displays the total inside #total-sales, and loads Bootstrap 5 from jsdelivr.",
    "checks": [
        "js: document.title === `Sales Summary ${seed}`",
        "js: !!document.querySelector(\"link[href*='bootstrap']\")",
        "js: Math.abs(parseFloat(document.querySelector(\"#total-sales\").textContent) - ${result}) < 0.01"
    ],
    "evaluation_url": "https://tds-proj1-llm-api.vercel.app/eval",
    "attachments": [
        {"name": "data.csv", "url": "data:text/csv;base64," + "${seed}"}
    ]
}

# Round 2 payload
payload2 = {
    "email": "student@example.com",
    "secret": "Jo1010",
    "task": "sum-of-sales",
    "round": 2,
    "nonce": "abcd1234",
    "brief": "Add a Bootstrap table #product-sales that lists each product with its total sales and keeps #total-sales accurate after render; introduce a currency select #currency-picker that converts the computed total using rates.json from attachments and mirrors the active currency inside #total-currency; allow filtering by region via #region-filter, update #total-sales with the filtered sum, and set data-region on that element to the active choice.",
    "checks": [
        "js: document.querySelectorAll(\"#product-sales tbody tr\").length >= 1",
        "js: (() => { const rows = [...document.querySelectorAll(\"#product-sales tbody tr td:last-child\")]; const sum = rows.reduce((acc, cell) => acc + parseFloat(cell.textContent), 0); return Math.abs(sum - ${result}) < 0.01; })()",
        "js: !!document.querySelector(\"#currency-picker option[value='USD']\")",
        "js: !!document.querySelector(\"#total-currency\")",
        "js: document.querySelector(\"#region-filter\").tagName === \"SELECT\"",
        "js: document.querySelector(\"#total-sales\").dataset.region !== undefined"
    ],
    "evaluation_url": "https://tds-proj1-llm-api.vercel.app/eval",
    "attachments": [
        {"name": "rates.json", "url": "data:application/json;base64," + "${seed}"}
    ]
}

# url = "http://127.0.0.2:8000/api/submit"
url = "https://tds-proj1-v2.vercel.app/api/submit"


# Send Round 1
r1 = requests.post(url, json=payload1)
print("Round 1 Response:")
print(r1.status_code)

time.sleep(120)

# Send Round 2
r2 = requests.post(url, json=payload2)
print("\nRound 2 Response:")
print(r2.status_code)