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
from nfz_api import find_available_visits, format_visit_results
# Import the Twilio SMS sender
from twilio_sms import TwilioSMS

load_dotenv()

@function_tool(
    name_override="visits", description_override="Lookup visits at the National Health Fund (NFZ)."
)
async def visits(province_code: province_codes, medical_service: benefit_names, user_name: str) -> str:
    """
    Look up available medical visits in the National Health Fund (NFZ)

    Here are mappings for province codes
    PROVINCES = {
    "01": "DOLNOŚLĄSKIE",
    "02": "KUJAWSKO-POMORSKIE",
    "03": "LUBELSKIE",
    "04": "LUBUSKIE",
    "05": "ŁÓDZKIE",
    "06": "MAŁOPOLSKIE",
    "07": "MAZOWIECKIE",
    "08": "OPOLSKIE",
    "09": "PODKARPACKIE",
    "10": "PODLASKIE",
    "11": "POMORSKIE",
    "12": "ŚLĄSKIE",
    "13": "ŚWIĘTOKRZYSKIE",
    "14": "WARMIŃSKO-MAZURSKIE",
    "15": "WIELKOPOLSKIE",
    "16": "ZACHODNIOPOMORSKIE",
    }
    
    Args:
        location: Location or province name/code
        medical_service: Type of medical service needed
        user_name: Name of the user requesting the visit
        
    Returns:
        Information about available visits
    """
    print(f"Checking NFZ API for {medical_service} in {province_code} for {user_name}")
    
    try:
        # Query the NFZ API for available visits
        queues = await find_available_visits(
            province=province_code,
            benefit=medical_service,
            for_children=False,
            limit=5
        )
        
        # Format the results
        result = format_visit_results(queues)
        
        # Count the number of visits found
        visit_count = len(queues) if queues else 0
        
        if visit_count > 0:
            return f"Hello {user_name}, I found {visit_count} available visits for {medical_service} in province {province_code}:\n\n{result}"
        else:
            return f"Hello {user_name}, I couldn't find any available visits for {medical_service} in province {province_code}."
    
    except Exception as e:
        print(f"Error querying NFZ API: {e}")
        return f"Sorry {user_name}, I couldn't find any available visits for {medical_service} in {province_code} due to an error."

@function_tool(
    name_override="send_sms_summary", description_override="Send a summary of available visits via SMS."
)
async def send_sms_summary(user_name: str, visit_results: str) -> str:
    """
    Send a summary of available visits to the user via SMS using Twilio.
    
    Args:
        user_name: Name of the user
        visit_results: The formatted visit results to send
        
    Returns:
        Confirmation message about the SMS status
    """
    # Access the caller number from the function's attribute
    phone_number = getattr(send_sms_summary, 'caller_number', "+48792174616")
    
    print(f"Preparing to send SMS to {phone_number} for {user_name}")
    
    try:
        # Create the SMS message content
        message = f"Hello {user_name}, here are your requested NFZ visits:\n\n{visit_results}\n\nThank you for using NFZ Assistant."
        
        # Initialize the Twilio SMS sender
        sms_sender = TwilioSMS(alpha_sender_id="AsystentNFZ")
        
        # Send the SMS
        result = sms_sender.send_sms(phone_number, message)
        
        print(f"SMS sent successfully! SID: {result['sid']}")
        return f"I've sent the available visits information to your phone number. Please check your messages."
    
    except Exception as e:
        error_message = f"Error sending SMS: {str(e)}"
        print(error_message)
        return f"I'm sorry, I couldn't send the SMS to {phone_number}. Please check if the number is correct and try again."
    
nfz_agent = Agent(
    name="NFZ Agent",
    handoff_description="A helpful agent that can answer questions about the NFZ.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a support agent. You need to gather information from the user. The user is a potential patient that needs to be scheduled for a health meeting.
        You use the tools given to you to gather information from the user.
        You call the relevant tools in order.

        
        There are three information points you need to gather:
        1. The user's name
        2. The user's type of medical need
        3. The user's preferred location for the meeting

        You will ask the user for each of these pieces of information in order.
        You will ask the user for their name first. Once you have the name, you will ask for the type of medical need. Once you have the type of medical need, you will ask for the preferred location.
        You will not ask for the user's name, type of medical need, or preferred location all at once. You will ask for each piece of information in order until you gather all three.
        You will not ask for the user's name, type of medical need, or preferred location in a single message.
        
        Once you gather all information, invoke the visits tool and check if there are visits available.
        
        After showing the available visits:
        1. Tell the user how many visits you found (this information is already included in the visits tool response)
        2. Ask the user if they would like to receive the information via SMS
        3. If the user confirms they want the information via SMS, use the send_sms_summary tool to send them the full visit details
        4. Pass the exact visit information from the visits tool response to the send_sms_summary tool
        
        Only send the SMS if the user explicitly confirms they want to receive it. Use phrases like "Would you like me to send these visit details to your phone via SMS?" to ask for confirmation.
    """,
    tools=[visits, send_sms_summary],
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