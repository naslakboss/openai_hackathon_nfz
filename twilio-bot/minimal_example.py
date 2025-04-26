from __future__ import annotations as _annotations

import asyncio
import uuid

from agents import (
    Agent,
    HandoffOutputItem,
    ItemHelpers,
    MessageOutputItem,
    Runner,
    ToolCallItem,
    ToolCallOutputItem,
    TResponseInputItem,
    function_tool,
    trace,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from dotenv import load_dotenv
from bot_types import benefit_names

# Import the NFZ API functions
from nfz_api import find_available_visits, format_visit_results

load_dotenv()

@function_tool(
    name_override="visits", description_override="Lookup visits at the National Health Fund (NFZ)."
)
async def visits(location: str, medical_service: benefit_names, user_name: str) -> str:
    """
    Look up available medical visits in the National Health Fund (NFZ)
    
    Args:
        location: Location or province name/code
        medical_service: Type of medical service needed
        user_name: Name of the user requesting the visit
        
    Returns:
        Information about available visits
    """
    print(f"Checking NFZ API for {medical_service} in {location} for {user_name}")
    
    try:
        # Query the NFZ API for available visits
        queues = await find_available_visits(
            province=location,
            benefit=medical_service,
            for_children=False,
            limit=5
        )
        
        # Format the results
        result = format_visit_results(queues)
        return f"Hello {user_name}, here are the available visits:\n\n{result}"
    
    except Exception as e:
        print(f"Error querying NFZ API: {e}")
        return f"Sorry {user_name}, I couldn't find any available visits for {medical_service} in {location} due to an error."

nfz_agent = Agent(
    name="NFZ Agent",
    handoff_description="A helpful agent that can answer questions about the NFZ.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a support agent. You need to gather information from the user. The user is a potential patient that needs to be scheduled for a health meeting.
        You use the tools given to you to gather information from the user.
        you call the relevant tools in order.

        
        There are three information points you need to gather:
        1. The user's name
        2. The user's type of medical need
        3. The user's preferred location for the meeting
        You will ask the user for each of these pieces of information in order.
        You will ask the user for their name first. Once you have the name, you will ask for the type of medical need. Once you have the type of medical need, you will ask for the preferred location.
        You will not ask for the user's name, type of medical need, or preferred location all at once. You will ask for each piece of information in order until you gather all three.
        You will not ask for the user's name, type of medical need, or preferred location in a single message.
        Once you gather all information invoke visits tool and check if there is a visit available.
    """,
    tools=[visits],
)

async def main():
    current_agent: Agent = nfz_agent
    input_items: list[TResponseInputItem] = []

    # Normally, each input from the user would be an API request to your app, and you can wrap the request in a trace()
    # Here, we'll just use a random UUID for the conversation ID
    conversation_id = uuid.uuid4().hex[:16]

    while True:
        user_input = input("Enter your message: ")
        with trace("Customer service", group_id=conversation_id):
            input_items.append({"content": user_input, "role": "user"})
            result = await Runner.run(current_agent, input_items)

            for new_item in result.new_items:
                agent_name = new_item.agent.name
                if isinstance(new_item, MessageOutputItem):
                    print(f"{agent_name}: {ItemHelpers.text_message_output(new_item)}")
                elif isinstance(new_item, HandoffOutputItem):
                    print(
                        f"Handed off from {new_item.source_agent.name} to {new_item.target_agent.name}"
                    )
                elif isinstance(new_item, ToolCallItem):
                    print(f"{agent_name}: Calling a tool")
                elif isinstance(new_item, ToolCallOutputItem):
                    print(f"{agent_name}: Tool call output: {new_item.output}")
                else:
                    print(f"{agent_name}: Skipping item: {new_item.__class__.__name__}")
            input_items = result.to_input_list()
            current_agent = result.last_agent


if __name__ == "__main__":
    asyncio.run(main())