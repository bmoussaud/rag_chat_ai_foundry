"""
Main entrypoint for RAG CHAT AI Foundry Chainlit frontend.
Starts Chainlit server and loads AI Agent Service agent.
"""
import os
import chainlit as cl
from rag_agent import UniversalRAGAgent

MODEL_NAME = os.getenv("MODEL_NAME", "universalragchat-gpt-4.1-mini")


@cl.on_message
async def main(message: cl.Message):
    """
    Handles incoming messages from Chainlit frontend and routes to AI Agent Service.
    """
    agent = UniversalRAGAgent()
    await agent.initialize()
    try:
        response = await agent.chat(message.content)
        await cl.Message(content=response).send()
    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()
