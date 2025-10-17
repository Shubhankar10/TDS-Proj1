# test_client.py
import requests
payload = {
    "email":"student@example.com",
    "secret":"Jo1010",
    "task":"Repo-Final",
    "round":1,
    "nonce":"ab12-3456",
    "brief":"Create a captcha solver",
    "checks":["Repo has MIT license","README.md is professional"],
    "evaluation_url":"http://127.0.0.1:9000/notify",
    "attachments":[
    {"name":"sample.txt","url":"data:text/plain;base64,SGVsbG8h"},
    {"name":"input.md","url":"data:text/markdown;base64,IyBIZWxsbyBNSUQ="},
    {"name":"data.csv","url":"data:text/csv;base64,Y29sdW1uMSxjb2x1bW4yCjEsMg=="},
    {"name":"rates.json","url":"data:application/json;base64,eyJ0ZXN0IjogInZhbHVlIn0="}
]

}


# {
# #   // Student email ID
#   "email": "student@example.com",
# #   // Student-provided secret
#   "secret": "...",
# #   // A unique task ID.
#   "task": "captcha-solver-...",
# #   // There will be multiple rounds per task. This is the round index
#   "round": 1,
# #   // Pass this nonce back to the evaluation URL below
#   "nonce": "ab12-...",
# #   // brief: mentions what the app needs to do
#   "brief": "Create a captcha solver that handles ?url=https://.../image.png. Default to attached sample.",
# #   // checks: mention how it will be evaluated
#   "checks": [
#     "Repo has MIT license"
#     "README.md is professional",
#     "Page displays captcha URL passed at ?url=...",
#     "Page displays solved captcha text within 15 seconds",
#   ],
# #   // Send repo & commit details to the URL below
#   "evaluation_url": "https://example.com/notify",
# #   // Attachments will be encoded as data URIs
#   "attachments": [{ "name": "sample.png", "url": "data:image/png;base64,iVBORw..." }]
# }


url = "http://127.0.0.2:8000/api/submit"
# url = "https://tds-proj1-llm-api.vercel.app/api/submit"

r = requests.post(url, json=payload)
print(r)
print(r.status_code)
# print( r.json())


# After local server run this to ping