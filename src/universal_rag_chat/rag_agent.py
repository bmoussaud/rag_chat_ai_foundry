"""
AI Agent Service integration for RAG CHAT AI Foundry.
Implements agent logic using provided model name.
"""
from configuration import settings, validate_required_settings
from opentelemetry import trace
from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

from azure.ai.projects import AIProjectClient
from typing import Dict, List, Optional, Any
import logging
import asyncio
import os
from chainlit.logger import logger
import httpx


# Configure logger for this module
logger = logging.getLogger("setlistfm_agent")
logger.setLevel(getattr(logging, settings.log_level))
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

# Optionally, reduce verbosity of Azure SDK logs
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
    logging.WARNING)


class UniversalRAGAgent:
    """AI Foundry Agent for universal RAG """

    def __init__(self):
        self.project_client: Optional[AIProjectClient] = None
        self.agents_client = None
        self.agent_id: Optional[str] = None
        self._initialized = False

        # Validate configuration
        validate_required_settings()

        # Configure telemetry
        self._configure_telemetry()

        # Set up Azure credentials
        if settings.azure_client_id:
            credential = ManagedIdentityCredential(
                client_id=settings.azure_client_id)
            logger.info(f"Using managed identity: {settings.azure_client_id}")
        else:
            credential = DefaultAzureCredential()
            logger.info("Using default Azure credential")

        logger.info("Initializing AI Project Client")
        self.project_client = AIProjectClient(
            endpoint=settings.project_endpoint,
            credential=credential
        )
        self.agents_client = self.project_client.agents

    async def available_models(self) -> List[Dict[str, Any]]:
        """Retrieve all available models in the project."""
        if not self._initialized:
            await self.initialize()

        try:
            models = []
            for d in self.project_client.deployments.list():
                logger.info(f"*** Found deployment: {d} ***")
                models.append({
                    "name": d.name,
                    "modelPublisher": d['modelPublisher'],
                    "modelName": d['modelName'],
                    "modelVersion": d['modelVersion']
                })
            return models
        except Exception as e:
            logger.error(f"Failed to retrieve models: {e}")
            return []

    async def initialize(self, model_name: Optional[str] = None):
        """Initialize the agent with Azure AI Foundry."""

        logger.info("Initializing Universal RAG Agent...")
        self._selected_model = self._get_model_by_name(
            model_name) or settings.model_deployment_name

        # Create the agent
        await self._create_agent()

        self._initialized = True
        logger.info("Universal RAG Agent initialized successfully")

    def _configure_telemetry(self):
        """Configure Application Insights telemetry."""
        if not settings.azure_monitor_enabled:
            logger.info("Azure Monitor telemetry is disabled")
            return

        try:
            if settings.applicationinsights_connection_string:
                logger.info("Configuring Application Insights...")

                # Enable content recording for AI interactions
                if settings.azure_tracing_content_recording:
                    os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true"

                # Configure Azure Monitor
                configure_azure_monitor(
                    connection_string=settings.applicationinsights_connection_string,
                    instrumentation_options={
                        "azure_sdk": {"enabled": True},
                        "fastapi": {"enabled": True},
                        "httpx": {"enabled": True},
                        "requests": {"enabled": True},
                        "asyncio": {"enabled": True}
                    }
                )

                # Instrument HTTP clients
                # HTTPXClientInstrumentor().instrument()
                # RequestsInstrumentor().instrument()
                # AsyncioInstrumentor().instrument()

                logger.info("Application Insights configured successfully")
            else:
                logger.warning(
                    "No Application Insights connection string provided")

        except Exception as e:
            logger.warning(f"Failed to configure telemetry: {e}")

    async def _create_agent(self):
        """Create the AI agent with Bing Grounding tool."""
        logger.info("Creating AI agent ...")

        try:
            self._delete_agent()  # Clean up any existing agent
            logger.info(
                f"Create agent with enhanced instructions using model: {self._selected_model}")
            agent = self.agents_client.create_agent(
                model=self._selected_model,
                name=f"universal-chat-agent-{self._selected_model}",
                instructions=self._get_agent_instructions(),
                tools=[],
                description="Universal RAG Chat Agent",
            )

            self.agent_id = agent.id
            logger.info(f"Created agent with ID: {self.agent_id}")

        except Exception as e:
            logger.error(f"Failed to create agent: {e}", exc_info=True)
            raise

    def _get_agent_instructions(self) -> str:
        """Get agent instructions for setlist content management."""
        return """
        You are a helpful AI agent designed to assist users.
        Your primary goal is to provide accurate and engaging responses based on the user's input.
        Always strive to be helpful, accurate, and engaging.
        """

    async def chat(self, message: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a chat message and return agent response."""
        if not self._initialized:
            await self.initialize()

        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span("universal_agent_chat") as span:
            span.set_attribute("message_length", len(message))

            try:
                logger.info(f"Processing chat message: {message[:100]}...")

                # Create or use existing thread
                if thread_id:
                    thread = self.agents_client.threads.get(
                        thread_id=thread_id)
                else:
                    thread = self.agents_client.threads.create()
                    thread_id = thread.id

                span.set_attribute("thread_id", thread_id)

                # Add user message to thread
                user_message = self.agents_client.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=message
                )

                # Create and process agent run
                run = self.agents_client.runs.create_and_process(
                    thread_id=thread_id,
                    agent_id=self.agent_id
                )

                span.set_attribute("run_status", run.status)

                if run.status == "failed":
                    error_msg = f"Agent run failed: {run.last_error}"
                    logger.error(error_msg)
                    span.set_attribute("error", error_msg)
                    return {
                        "thread_id": thread_id,
                        "response": "I encountered an error processing your request. Please try again.",
                        "status": "error"
                    }

                # Get agent response
                messages = self.agents_client.messages.list(
                    thread_id=thread_id)

                # Find the latest assistant message
                response_content = ""
                citations = []

                for msg in messages:
                    if msg.role == "assistant":
                        if msg.text_messages:
                            for text_msg in msg.text_messages:
                                response_content = text_msg.text.value
                                break
                        break

                # Collect citations if available
                for msg in messages:
                    if msg.role == "assistant":
                        for annotation in msg.url_citation_annotations:
                            citations.append({
                                "title": annotation.url_citation.title,
                                "url": annotation.url_citation.url
                            })

                logger.info(
                    f"Generated response with {len(citations)} citations")

                return {
                    "thread_id": thread_id,
                    "response": response_content,
                    "citations": citations,
                    "status": "success"
                }

            except Exception as e:
                error_msg = f"Error in chat processing: {e}"
                logger.error(error_msg)
                span.set_attribute("error", error_msg)

                return {
                    "thread_id": thread_id,
                    "response": "I encountered an error processing your request. Please try again later.",
                    "status": "error"
                }

    async def get_thread_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a specific thread."""
        if not self._initialized:
            await self.initialize()

        try:
            messages = self.agents_client.messages.list(thread_id=thread_id)

            history = []
            for msg in messages:
                content = ""
                if msg.text_messages:
                    for text_msg in msg.text_messages:
                        content = text_msg.text.value
                        break

                history.append({
                    "role": msg.role,
                    "content": content,
                    "timestamp": msg.created_at
                })

            # Reverse to get chronological order
            return list(reversed(history))

        except Exception as e:
            logger.error(f"Error getting thread history: {e}")
            return []

    def _get_model_by_name(self, model_name: Optional[str]) -> Optional[str]:
        """
        Retrieve the deployment name for a given model name.
        Returns the deployment name if found, otherwise None.
        """
        logger.info(f"Retrieving model by name: {model_name}")
        if not model_name:
            return None
        try:
            for d in self.project_client.deployments.list():
                if d['modelName'] == model_name:
                    logger.info(f"Found model: {d['name']}")
                    return d['name']
        except Exception as e:
            logger.error(
                f"Error retrieving model by name: {e}, returning None")
        return None

    def _delete_agent(self):
        """Delete the agent if it exists."""
        if not self.agent_id:
            logger.warning("No agent ID set, skipping deletion")
            return

        try:
            logger.info(f"Deleting agent with ID: {self.agent_id}")
            self.agents_client.delete_agent(self.agent_id)
            logger.info("Agent deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete agent: {e}", exc_info=True)

    async def shutdown(self):
        """Clean up resources."""
        logger.info("Shutting down SetlistFM Agent...")

        try:
            # Delete the agent
            self._delete_agent()

            # Close project client
            if self.project_client:
                self.project_client.close()

            self._initialized = False
            logger.info("SetlistFM Agent shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
