# app.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from llm import initialize_llm_client
from Code import AckResponse, RequestPayload, EvalPayload, round_1_pipeline,round_2_pipeline
from fastapi import BackgroundTasks
import time

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


TASK_ROUNDS = {}  # key: task, value: dict with round1_data and completion flag

@app.post("/api/submit", response_model=AckResponse)
async def submit(payload: RequestPayload, background_tasks: BackgroundTasks):
    print("[Submit]")

    if payload.secret != EXPECTED_SECRET:
        print("[Submit] Invalid Secret 401")
        raise HTTPException(status_code=401, detail="invalid secret")
    
    if payload.task not in TASK_ROUNDS:
        TASK_ROUNDS[payload.task] = {"round1_done": False, "round1_data": None}

    # Immediate ack response
    ack = AckResponse(
        task=payload.task,
        round=payload.round,
    )
    print("[Submit] Response 200")

    # Schedule pipeline to run in the background

    def run_pipeline(payload):
        initialize_llm_client()
        task_state = TASK_ROUNDS[payload.task]

        if payload.round == 1:
            print("[Round 1 Pipeline]")
            data = round_1_pipeline(payload)
            print("[Round 1] Done.")
            task_state["round1_data"] = data
            task_state["round1_done"] = True

        elif payload.round == 2:
            print("[Round 2 Pipeline]")
            # Wait until round1 is done
            while not task_state["round1_done"]:
                print("Waiting for Round 1.")
                time.sleep(5)
            print("Moving to Round 2")
            round_2_pipeline(payload, task_state["round1_data"])
            print("[Round 2] Done.")

    background_tasks.add_task(run_pipeline, payload)

    return ack



@app.post("/eval", response_class=HTMLResponse)
async def eval_endpoint(payload: EvalPayload):
    # Convert payload to dict for printing and display
    payload_dict = payload.dict()
    
    # Print to console
    print("Received payload")
    
    # Return formatted HTML response
    html_content = "<h2>Received JSON Payload:</h2><pre>{}</pre>".format(payload_dict)
    return HTMLResponse(content=html_content)

