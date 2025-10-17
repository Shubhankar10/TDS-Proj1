import os
from dotenv import load_dotenv  
load_dotenv()
from openai import OpenAI

llm_client = None

def initialize_llm_client():
    global llm_client
    llm_client = LLMClient(api_key=os.getenv("LLM_API_KEY"))
    print("[LLM] Client Initialized")



class LLMClient:
    def __init__(self, base_url: str = "https://integrate.api.nvidia.com/v1",api_key: str = None):
        if not api_key:
            raise ValueError("LLM_API_KEY not found in environment. Check your .env file.")

        print("[LLMClient] Initializing client.")
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        print("[LLMClient] Client initialized successfully.")


    def query(self, user_input: str, model: str = "deepseek-ai/deepseek-v3.1") -> str:
        # print(f"[LLMClient] Query started: '{user_input}'")
        print(f"[LLMClient] Query sent to model.")
        completion = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user_input}],
            temperature=0.2,
            top_p=0.7,
            max_tokens=8192,
            extra_body={"chat_template_kwargs": {"thinking": True}},
            stream=True
        )

        response_text = ""
        reasoning_text = ""

        print("[LLMClient] Receiving streamed response.")
        for chunk in completion:
            reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
            if reasoning:
                reasoning_text += reasoning
            if chunk.choices[0].delta.content is not None:
                response_text += chunk.choices[0].delta.content

        print("[LLMClient] Query completed.")
        return response_text.strip()



def ask_llm(query: str) -> str:
    if llm_client is None:
        print("[LLM] Initialized New Client")
        initialize_llm_client()
    print("[ASK LLM]")
    response = llm_client.query(query)
    # response = "<html>Pass</html>"
    return response


# llm_client = LLMClient(api_key=os.getenv("LLM_API_KEY"))
# print(ask_llm("Give pythoncode to return a strinf"))