import os
import uuid
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from google.adk.tools import AgentTool
from google.adk import Agent, Runner 
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
import prompts  # Ensure this file defines DEFAULT_INSTRUCTION_CALL and DEFAULT_INSTRUCTION_SEARCH
import requests

# === Tool Function ===
def call_person(name: str, tool_context: ToolContext):
    number_map = {
        "Nikunj": os.getenv("NIKUNJ_PHONE"),
        "Vidhi": os.getenv("VIDHI_PHONE")
    }

    if name not in number_map:
        return {"error": f"Name '{name}' not recognized. Allowed: {', '.join(number_map.keys())}"}

    payload = {
        "customers": [
            {
                "number": number_map[name],
                "name": name,
                "numberE164CheckEnabled": True
            }
        ],
        "assistant": {
            "voice": {
                "provider": "azure",
                "voiceId": os.getenv("VOICE_ID", "andrew")
            }
        },
        "phoneNumber": {
            "twilioAccountSid": os.getenv("TWILIO_SID"),
            "twilioPhoneNumber": os.getenv("TWILIO_NUMBER"),
            "twilioAuthToken": os.getenv("TWILIO_AUTH")
        }
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('VAPI_TOKEN')}"
    }

    response = requests.post("https://api.vapi.ai/call", headers=headers, json=payload)
    try:
        data = response.json()
    except Exception:
        return {
            "status": "Error",
            "error": "Failed to parse JSON",
            "details": response.text
        }

    results = data.get("results", [])
    if results and results[0].get("status") == "queued":
        print(f"✅ Call to {name} successfully queued.")
        return {
            "status": "Call queued",
            "call_id": results[0]["id"],
            "listen_url": results[0]["monitor"]["listenUrl"],
            "control_url": results[0]["monitor"]["controlUrl"]
        }
    else:
        return {
            "status": "Call not queued",
            "details": data
        }

# === Load Environment ===
load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "❌ GOOGLE_API_KEY is missing from .env"

# === Config ===
MODEL = "gemini-2.5-flash"
APP_NAME = "alexa_gemini_agent"
USER_ID = "alexa_user"

# === Agents ===
Agent_Call = Agent(
    model=MODEL,
    name='CallAgent',
    description="This agent can call people using the VAPI service.",
    instruction=prompts.DEFAULT_INSTRUCTION_CALL,
    tools=[call_person]
)

Agent_Search = Agent(
    model=MODEL,
    description="This agent can answer general queries augmented by web search using Google.",
    name='SearchAgent',
    instruction=prompts.DEFAULT_INSTRUCTION_SEARCH,
    tools=[google_search]
)

alexa_root_agent = Agent(
    model=MODEL,
    description="This is the root agent for Alexa. It can call people or search the web.",
    name="alexa_root_agent",
    instruction="You have superpowers to call people. When asked to call someone invoke Agent_Call subagent and return its response as is. Otherwise, use Agent_Search for other queries.",
    tools=[AgentTool(agent=Agent_Call), AgentTool(agent=Agent_Search)],
    output_key="answer"
)

session_service = InMemorySessionService()
runner = Runner(agent=alexa_root_agent, app_name=APP_NAME, session_service=session_service)

# === FastAPI Server ===
app = FastAPI()

@app.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        query = body.get("query", "").strip()

        if not query:
            return JSONResponse({"error": "Missing 'query' field."}, status_code=400)

        session_id = f"session_{uuid.uuid4().hex[:8]}"
        await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)

        content = types.Content(role="user", parts=[types.Part(text=query)])
        final_response = "Sorry, no response generated."

        async for event in runner.run_async(user_id=USER_ID, session_id=session_id, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                final_response = event.content.parts[0].text.strip()

        return JSONResponse({"response": final_response})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# === Uvicorn Launch (Only when run directly) ===
if __name__ == "__main__":
    import uvicorn
    print("✅ Agent API.py booted")
    print("🔑 GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY")[:6], "...")  # Masked output
    uvicorn.run("Agent API:app", host="0.0.0.0", port=8000)
