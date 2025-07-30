# Agent-on-Alexa
This Repository is a Tutorial on how I pushed AI Agentics to my Alexa via Skills

Overall Idea

<img width="1180" height="509" alt="image" src="https://github.com/user-attachments/assets/b9a1d538-3aeb-4059-b7f2-a2512bc7060c" />

# 🤖 Gemini Agentic Server with Calling Support (Step 1)

This repo sets up a FastAPI server hosting a Gemini-powered agent that can:
- Answer general queries using **Google Search**
- **Place phone calls** via **Vapi.ai** using your **Twilio** number

✅ **This is Step 1** of a two-part system. Step 2 (Alexa skill integration via Lambda) will be added in the next iteration.

---

## 🧭 Step-by-Step Setup

### 🧠 Step 1.1: Create a Google Search Agent

1. Set up your environment with Google ADK.
2. Create an agent (`Agent_Search`) that uses `google_search` as a tool.
3. Use a basic prompt like:

```python
instruction="You are a helpful assistant that uses web search to answer user questions truthfully."
```

4. Test that it returns web-augmented responses.

---

### 📞 Step 1.2: Enable Outbound Calling

#### 1. Set up a free Twilio account:
- [twilio.com](https://www.twilio.com/)
- Get a **Twilio phone number**
- Note your:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - Twilio number (e.g. `+1XXXXXXXXXX`)
- Verify any personal numbers you want to call

#### 2. Set up Vapi.ai:
- [vapi.ai](https://vapi.ai)
- Add your Twilio number to the platform
- Create any agent (a basic default is fine)
- Go to **API > Generate Snippet**
- Copy the JSON payload and adapt it (as shown in `call_person` function)
- Replace your phone number and auth fields with `os.getenv(...)` for security

---

### 🧩 Step 1.3: Convert to AgentTools

- Wrap your `call_person()` function into a `Tool`
- Add it to a subagent: `Agent_Call`
- Now, create a parent agent `alexa_root_agent` like this:

```python
Agent(
    model="gemini-2.5-flash",
    name="alexa_root_agent",
    instruction="Use Agent_Call if asked to call someone, else use Agent_Search.",
    tools=[AgentTool(agent=Agent_Call), AgentTool(agent=Agent_Search)],
    output_key="answer"
)
```

---

### ☁️ Step 1.4: Host the Agent on EC2

1. Launch a **Ubuntu EC2 instance** on AWS (recommended).
2. In **Security Groups**, allow inbound traffic on port `8000`.
3. SSH into the instance and:
   ```bash
   git clone <this-repo-url>
   cd <repo-folder>
   pip install -r requirements.txt
   ```

4. Start the FastAPI server in background:
   ```bash
   nohup python3 agent_server.py > server.log 2>&1 &
   ```

5. Confirm it's live:
   ```bash
   curl http://<your-ec2-ip>:8000/chat -X POST -H "Content-Type: application/json" -d '{"query": "who is the president of France?"}'
   ```

---

### 🔐 Environment Setup

Create a `.env` file (or set these as Lambda/EC2 env variables):

```env
GOOGLE_API_KEY=your_google_api_key
VAPI_TOKEN=your_vapi_api_key
TWILIO_SID=your_twilio_sid
TWILIO_AUTH=your_twilio_auth
TWILIO_NUMBER=+1XXXXXXXXXX
NIKUNJ_PHONE=+91XXXXXXXXXX
VIDHI_PHONE=+91XXXXXXXXXX
```

---
# 🔁 Step 2: Connecting Alexa to Your Gemini Agent via Lambda

This guide builds on **Step 1**, where your agentic Gemini FastAPI server is already live on EC2. Now, you will connect it to **Alexa** using a **Lambda function**.

---

## 🛠️ Step 2.1: Create & Deploy a Lambda Function

1. Go to [AWS Lambda Console](https://console.aws.amazon.com/lambda/).
2. Create a function named `Alexa` and upload the `lambda_function.py` from this repo.
3. Note the **Function ARN** from the overview screen.
4. Paste this **ARN** into the **Alexa Developer Console** under:
   ```
   Endpoint → Service Endpoint Type → AWS Lambda ARN → Default Region
   ```

📸 _As shown in the screenshots above, you can copy the ARN and paste it in all optional fields for safety._

---

## 📦 Step 2.2: Add Required Python Libraries as Lambda Layers

Lambda doesn’t support `pip install` like local dev. Instead:

### Required Libraries:
- `ask-sdk-model`
- `ask-sdk-core`
- `requests`

You’ll find these 3 ZIPs in the repo:

```
ask-sdk-model_layer.zip
ask-sdk-core_layer.zip
requests_layer.zip
```

🧩 To add them:
1. Go to the **Layers** tab under your Lambda function.
2. Click **Add a layer > Create a new layer**
3. Upload each zip, give it a name (e.g., `ask-core-layer`)
4. Choose Python runtime: `Python 3.11`
5. Attach all layers to your Lambda function.

_💡 We used Python 3.11 to match local development and Lambda runtime (you can set it via CLI if needed)._

---

## 🧪 Step 2.3: Test Your Lambda + Alexa Skill

Once layers are added and ARN is set:
- Go to Alexa Developer Console
- Use **Alexa Simulator** or your Echo device
- Try something like:

> “Alexa, ask Jarvis what is the capital of France?”

---

## 🧠 Step 2.4: Setup Invocation Name & Sample Intents

Sample configuration for `interactionModel`:

```json
{
  "interactionModel": {
    "languageModel": {
      "invocationName": "jarvis buddy",
      "intents": [
        {
          "name": "AMAZON.CancelIntent",
          "samples": []
        },
        {
          "name": "AMAZON.HelpIntent",
          "samples": []
        },
        {
          "name": "AMAZON.StopIntent",
          "samples": []
        },
        {
          "name": "AMAZON.NavigateHomeIntent",
          "samples": []
        },
        {
          "name": "JarvisQueryIntent",
          "slots": [
            {
              "name": "query",
              "type": "AMAZON.SearchQuery"
            }
          ],
          "samples": [
            "ask jarvis who is {query}",
            "Alexa ask jarvis {query}",
            "ask jarvis what is {query}",
            "ask jarvis tell me about {query}",
            "jarvis who is {query}",
            "jarvis what is {query}",
            "jarvis tell me about {query}",
            "can jarvis explain {query}",
            "jarvis {query}",
            "find out about {query} with jarvis"
          ]
        }
      ],
      "types": []
    }
  }
}
```

---

✅ That’s it! You now have:
- EC2-hosted Gemini agent server
- Alexa skill connected via Lambda
- Sample queries and calling support

Ready to talk to your own AI butler!



