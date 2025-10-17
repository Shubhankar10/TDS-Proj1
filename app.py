# app.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from llm import initialize_llm_client
from Code import AckResponse, RequestPayload, EvalPayload, round_1_pipeline,round_2_pipeline
from fastapi import BackgroundTasks


EXPECTED_SECRET = "Jo1010"


app = FastAPI(title="NewProj")

class Item(BaseModel):
    name: str
    value: int

# --- GET routes ---
@app.get("/")
def read_root():
    print("GET / called")
    return {"message": "Hello from Fast API!"}

@app.get("/hello")
def say_hello():
    print("GET /hello called")
    return {"greet": "Hi there!"}


# @app.post("/api/submit", response_model=AckResponse)
# def submit(payload: RequestPayload):
#     print("[Submit]")

#     if payload.secret != EXPECTED_SECRET:
#         print("[Submit] Invalid Secret 401")
#         raise HTTPException(status_code=401, detail="invalid secret")

#     # Immediate ack response
#     ack = AckResponse(
#         task=payload.task,
#         round=payload.round,
#     )
#     print("[Submit] Repsonse 200")

#     #Send ACK rest only pipeline code in background


#     print("[Submit] Initializing LLM")
#     initialize_llm_client()

#     if payload.round == 1:
#         print("[APP TO CODE : Round 1]")
#         round_1_pipeline(payload)
#     else:
#         print("[APP TO CODE : Round 1]")
#         round_2_pipeline(payload)
#     #Send to Eval

#     return ack


@app.post("/api/submit", response_model=AckResponse)
async def submit(payload: RequestPayload, background_tasks: BackgroundTasks):
    print("[Submit]")

    if payload.secret != EXPECTED_SECRET:
        print("[Submit] Invalid Secret 401")
        raise HTTPException(status_code=401, detail="invalid secret")

    # Immediate ack response
    ack = AckResponse(
        task=payload.task,
        round=payload.round,
    )
    print("[Submit] Response 200")

    # Schedule pipeline to run in the background
    def run_pipeline(payload):
        print("[Submit] Initializing LLM")
        initialize_llm_client()
        if payload.round == 1:
            print("[APP TO CODE : Round 1]")
            round_1_pipeline(payload)
        else:
            print("[APP TO CODE : Round 2]")
            round_2_pipeline(payload)

    background_tasks.add_task(run_pipeline, payload)

    return ack


@app.post("/eval", response_class=HTMLResponse)
async def eval_endpoint(payload: EvalPayload):
    # Convert payload to dict for printing and display
    payload_dict = payload.dict()
    
    # Print to console
    print("Received payload:", payload_dict)
    
    # Return formatted HTML response
    html_content = "<h2>Received JSON Payload:</h2><pre>{}</pre>".format(payload_dict)
    return HTMLResponse(content=html_content)

