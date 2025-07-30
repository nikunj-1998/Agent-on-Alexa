# -*- coding: utf-8 -*-
import logging
import os
import ask_sdk_core.utils as ask_utils
import requests
import traceback

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

# --- Logging Setup ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("✅ Lambda invoked with intent JarvisQueryIntent")

# --- EC2 Agent Endpoint (use environment variable for safety) ---
AGENT_URL = os.getenv("AGENT_SERVER_URL", "http://localhost:8000/chat")

# --- Intent: JarvisQueryIntent ---
class JarvisQueryIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("JarvisQueryIntent")(handler_input)

    def handle(self, handler_input):
        try:
            query = handler_input.request_envelope.request.intent.slots["query"].value
            logger.info(f"📡 Sending query to backend server: {query}")

            response = requests.post(AGENT_URL, json={"query": query}, timeout=30)

            if response.status_code == 200:
                result = response.json().get("response", "I didn't get a valid answer.")
                if not result.strip().endswith((".", "?", "!", "…")):
                    result = result.strip() + "."
                result += " Would you like to ask something else?"
            else:
                logger.error(f"❌ Backend server error {response.status_code}: {response.text}")
                result = "There was a problem reaching the backend. Try again later."

            return handler_input.response_builder.speak(result[:750]).ask("Anything else?").response

        except Exception as e:
            logger.exception("💥 Exception during API forwarding")
            return handler_input.response_builder.speak(
                f"Something went wrong: {type(e).__name__}"
            ).ask("Want to try again?").response

# --- Standard Intents ---
class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.speak("Hello, ask me anything.").ask("What would you like to know?").response

class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (
            ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input)
            or ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input)
        )

    def handle(self, handler_input):
        return handler_input.response_builder.speak("Goodbye!").response

class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.speak(
            "I didn’t understand that. Try again."
        ).ask("What would you like to ask?").response

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response

# --- Catch-All Error Handler ---
class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        error_trace = traceback.format_exc()
        logger.error("🔥 Unexpected error:\n" + error_trace)

        debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        if debug_mode:
            speak_output = f"{type(exception).__name__}: {str(exception)}"
        else:
            speak_output = "Sorry, something went wrong."

        return (
            handler_input.response_builder
            .speak(speak_output[:700])
            .ask("Would you like to try again?")
            .response
        )

# --- Register Handlers ---
sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(JarvisQueryIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
