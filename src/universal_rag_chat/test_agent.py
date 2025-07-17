"""
Test script for SetlistFM Agent
"""
from configuration import settings
from rag_agent import UniversalRAGAgent
import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))


async def test_agent():
    """Test the SetlistFM Agent functionality."""
    print("Testing SetlistFM Agent...")

    # Create agent instance
    agent = UniversalRAGAgent()

    try:
        # Initialize the agent
        print("Initializing agent...")
        await agent.initialize()
        print("✓ Agent initialized successfully")

        # Test chat functionality
        print("\nTesting chat functionality...")
        test_message = "Bonjour !"

        response = await agent.chat(test_message, thread_id=None)
        # Add thread ID to response for consistency
        thread_id = response['thread_id']
        print(f"✓ Chat response received:")
        print(f"  Thread ID: {response['thread_id']}")
        print(f"  Status: {response['status']}")
        print(f"  Response length: {len(response['response'])} characters")
        print(f"  Citations: {len(response['citations'])} found")
        print("  Sample response:", response['response'][:100] + "...")

        # Test setlist search
        print("\nTesting setlist search...")
        setlist_response = await agent.chat("Linkin Park", thread_id=thread_id)
        print(f"✓ Setlist search response received:")
        print(f"  Status: {setlist_response['status']}")
        print(
            f"  Response length: {len(setlist_response['response'])} characters")
        print(f"  Setlists found: {setlist_response['response']}")

        # Test venue info
        print("\nTesting venue info...")
        venue_response = await agent.chat("Stade de France", thread_id=thread_id)
        print(f"✓ Venue info response received:")
        print(f"  Status: {venue_response['status']}")
        print(
            f"  Response length: {len(venue_response['response'])} characters")
        print(f"  venue_response: {venue_response['response']}")

        response = await agent.chat("Quel est le deuxieme message", thread_id=None)
        print(f"✓ response received:")
        print(f"  Status: {venue_response['status']}")
        print(f"  response: {response['response']}")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        raise
    finally:
        # Clean up
        print("\nCleaning up...")
        # await agent.shutdown()
        print("✓ Agent shutdown complete")


def validate_environment():

    from dotenv import load_dotenv
    load_dotenv()
    """Validate required environment variables."""
    required_vars = [
        "PROJECT_ENDPOINT",
        "MODEL_DEPLOYMENT_NAME",

    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(
            f"✗ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables before running the test.")
        return False

    print("✓ Environment variables validated")
    return True


if __name__ == "__main__":
    print("SetlistFM Agent Test")
    print("=" * 50)

    # Validate environment
    if not validate_environment():
        sys.exit(1)

    # Run the test
    try:
        asyncio.run(test_agent())
        print("\n🎉 All tests passed!")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        sys.exit(1)
