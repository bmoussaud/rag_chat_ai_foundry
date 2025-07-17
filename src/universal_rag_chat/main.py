"""
Main entrypoint for RAG CHAT AI Foundry Chainlit frontend.
Starts Chainlit server and loads AI Agent Service agent.
"""
import os
import logging
import chainlit as cl
from rag_agent import UniversalRAGAgent

MODEL_NAME = os.getenv("MODEL_NAME", "universalragchat-gpt-4.1-mini")

agent = UniversalRAGAgent()

# Configure root logger for the application
logger = logging.getLogger("setlist_agent")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session with welcome message and authentication status."""
    logger.info("Chat session started.")
    chat_profile = cl.user_session.get("chat_profile")
    logger.info(f"Chat profile: {chat_profile}")
    await agent.initialize()


@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="GPT-3.5",
            markdown_description="The underlying LLM model is **GPT-3.5**.",
            icon="https://picsum.photos/200",
        ),
        cl.ChatProfile(
            name="GPT-4",
            markdown_description="The underlying LLM model is **GPT-4**.",
            icon="https://picsum.photos/250",
        ),
    ]


@cl.on_message
async def main(message: cl.Message):
    """
    Handles incoming messages from Chainlit frontend and routes to AI Agent Service.
    """
    try:
        thread_id = cl.user_session.get("thread_id", None)
        response = await agent.chat(message.content, thread_id=thread_id)
        logger.info(f"Response from agent: {response}")
        await cl.Message(content=response['response']).send()
        cl.user_session.set("thread_id", response['thread_id'])
    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()
