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
from bot_types import benefit_names, province_codes

# Import the NFZ API functions
from nfz_api import find_available_visits, format_visit_results, verify_locality_province, find_province_for_locality

load_dotenv()

@function_tool(
    name_override="find_province", description_override="Find province code for a locality."
)
async def find_province(locality: str) -> str:
    """
    Find the province code for a given locality
    
    Args:
        locality: Name of the locality (city)
        
    Returns:
        Information about the province
    """
    print(f"Finding province for locality '{locality}'")
    
    try:
        # Call the province finder function
        result = await find_province_for_locality(locality)
        
        if result["found"]:
            return f"✅ {result['message']}\nProvince code: {result['province_code']}"
        else:
            return f"❌ {result['message']}\nPlease check the spelling or try another nearby city."
    
    except Exception as e:
        print(f"Error finding province: {e}")
        return f"❌ Error while finding province: {str(e)}"

@function_tool(
    name_override="visits", description_override="Lookup visits at the National Health Fund (NFZ)."
)
async def visits(medical_service: benefit_names, locality: str, user_name: str) -> str:
    """
    Look up available medical visits in the National Health Fund (NFZ)
    
    Args:
        medical_service: Type of medical service needed
        locality: Locality or city name
        user_name: Name of the user requesting the visit
        
    Returns:
        Information about available visits
    """
    print(f"Looking up visits for {medical_service} in {locality} for {user_name}")
    
    try:
        # First find the province code for the locality
        province_result = await find_province_for_locality(locality)
        
        if not province_result["found"]:
            return f"Sorry {user_name}, I couldn't find your city '{locality}' in our system. Please check the spelling or try a nearby larger city."
        
        province_code = province_result["province_code"]
        province_name = province_result["province_name"]
        
        print(f"Found province for {locality}: {province_name} (code: {province_code})")
        
        # Query the NFZ API for available visits
        queues = await find_available_visits(
            province=province_code,
            benefit=medical_service,
            locality=locality,
            for_children=False,
            limit=5
        )
        
        # Format the results
        result = format_visit_results(queues)
        return f"Hello {user_name}, I found these available appointments for {medical_service} in {locality}, {province_name}:\n\n{result}"
    
    except Exception as e:
        print(f"Error querying NFZ API: {e}")
        return f"Sorry {user_name}, I couldn't find any available visits at this time. Please try again later or call our help line."

nfz_agent = Agent(
    name="NFZ Agent",
    model="gpt-4o",
    handoff_description="A helpful agent that can answer questions about the NFZ.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a friendly support agent for the National Health Fund helping seniors schedule medical appointments. You speak in a warm, clear, and simple manner.
    
    Keep your messages short and use simple language. Speak slowly and clearly. Avoid complicated terms. Repeat important information.
    
    You need to gather only three pieces of information:
    1. The person's first name
    2. What type of doctor they need to see
    3. What city they live in
    
    Important rules for voice interaction with seniors:
    - Ask only ONE question at a time
    - Wait for a complete answer before moving to the next question
    - Speak in short, simple sentences
    - Be patient and repeat information if needed
    - Offer help when the senior seems confused
    - Confirm information before proceeding
    
    Follow this exact order:
    1. First, introduce yourself briefly and ask for their first name only
    2. Thank them and ask what type of medical service they need
    3. Ask what city they live in
    
    Once you have all three pieces of information, use the visits tool to find available appointments.
    Present the results clearly, focusing on location, date and contact information.
    """,
    tools=[find_province, visits],
)

async def main():
    current_agent: Agent = nfz_agent
    input_items: list[TResponseInputItem] = []

    # Normally, each input from the user would be an API request to your app, and you can wrap the request in a trace()
    # Here, we'll just use a random UUID for the conversation ID
    conversation_id = uuid.uuid4().hex[:16]

    while True:
        user_input = input("Enter your message: ")
        with trace("NFZ Agent", group_id=conversation_id):
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