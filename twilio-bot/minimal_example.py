from __future__ import annotations as _annotations

import asyncio
import uuid
import time
import logging

from agents import (
    Agent,
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
from twilio_sms import TwilioSMS

# Configure logging to reduce verbosity
logging.basicConfig(level=logging.WARNING)
logging.getLogger('agents').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
from nfz_api import find_available_visits, format_visit_results, find_province_for_locality

load_dotenv()

@function_tool(
    name_override="find_province", description_override="Find province code for a locality. It should always be in polish example: 'Warszawa'"
)
async def find_province(locality: str) -> str:
    """
    Find the province code for a given locality
    
    Args:
        locality: Name of the locality (city). It should always be in polish example: "Warszawa"
        
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
async def visits(medical_service: benefit_names, locality: str) -> str:
    """
    Look up available medical visits in the National Health Fund (NFZ)
    
    Args:
        medical_service: Type of medical service needed
        locality: Locality or city name
        
    Returns:
        Information about available visits
    """
    print(f"Looking up visits for {medical_service} in {locality}")
    
    try:
        # First find the province code for the locality
        province_result = await find_province_for_locality(locality)
        
        if not province_result["found"]:
            return f"Sorry, I couldn't find your city '{locality}' in our system. Please check the spelling or try a nearby larger city."
        
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
        
        # Count the number of visits found
        visit_count = len(queues) if queues else 0
        
        if visit_count > 0:
            return f"Hello User, I found {visit_count} available visits for {medical_service} in province {province_code}:\n\n{result}"
        else:
            return f"Hello User, I couldn't find any available visits for {medical_service} in province {province_code}."
    
    except Exception as e:
        print(f"Error querying NFZ API: {e}")
        return f"Sorry, I couldn't find any available visits at this time. Please try again later or call our help line."

@function_tool(
    name_override="send_sms_summary", description_override="Send a summary of available visits via SMS."
)
async def send_sms_summary(visit_results: str) -> str:
    """
    Send a summary of available visits to the user via SMS using Twilio.
    
    Args:
        
        visit_results: The formatted visit results to send
        
    Returns:
        Confirmation message about the SMS status
    """
    user_name = "User"
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
    model="gpt-4o",
    handoff_description="A helpful agent that can answer questions about the NFZ.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a friendly support agent for the National Health Fund helping seniors schedule medical appointments. You speak in a warm, clear, and simple manner.
    
    Keep your messages short and use simple language. Speak slowly and clearly. Avoid complicated terms. Repeat important information.
    
    You need to gather two pieces of information:    
    1. What type of doctor they need to see
    2. What city they live in
    
    Important rules for voice interaction with seniors:
    - Ask only ONE question at a time
    - Wait for a complete answer before moving to the next question
    - Speak in short, simple sentences
    - Be patient and repeat information if needed
    - Offer help when the senior seems confused
    - Confirm information before proceeding
    
    Follow this exact order:
    1. First, introduce yourself briefly and ask what type of medical service they need
    2. Ask what city they live in
    
    Once you have both pieces of information, use the visits tool to find available appointments.
    Present the results clearly, focusing on location, date and contact information.
    
    # Structured output
    You will return the information in a structured format.
    Information about first 3 available visits structured as

    Nazwa Poradni: Poradnia Laryngologiczna
    Miasto: Poznań
    Numer: 510123456

    After showing the available visits:
    1. Tell the user how many visits you found (this information is already included in the visits tool response)
    2. Ask the user if they would like to receive the information via SMS
    3. If the user confirms they want the information via SMS, use the send_sms_summary tool to send them the full visit details
    4. Pass the exact visit information from the visits tool response to the send_sms_summary tool
    
    Only send the SMS if the user explicitly confirms they want to receive it. Use phrases like "Would you like me to send these visit details to your phone via SMS?" to ask for confirmation.
    """,
    tools=[find_province, visits, send_sms_summary],
)

async def main():
    current_agent: Agent = nfz_agent
    input_items: list[TResponseInputItem] = []
    
    # Generate a conversation ID
    conversation_id = uuid.uuid4().hex[:16]
    
    # Start with an empty input to get the initial AI message
    print("\n=== NFZ Health Fund Assistant ===")
    print("Starting conversation...\n")
    
    # Add an initial input to start the conversation
    input_items.append({"content": "", "role": "user"})
    
    # Get the initial AI message
    with trace("NFZ Agent", group_id=conversation_id):
        result = await Runner.run(current_agent, input_items)
        
        for new_item in result.new_items:
            agent_name = new_item.agent.name
            if isinstance(new_item, MessageOutputItem):
                print(f"{agent_name}: {ItemHelpers.text_message_output(new_item)}")
            elif isinstance(new_item, ToolCallItem):
                print(f"{agent_name}: Calling a tool...")
            elif isinstance(new_item, ToolCallOutputItem):
                print(f"{agent_name}: Tool call completed")
            else:
                print(f"{agent_name}: Processing...")
        
        input_items = result.to_input_list()
        current_agent = result.last_agent
    
    # Main conversation loop
    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("\nThank you for using the NFZ Health Fund Assistant. Goodbye!")
            break
        
        # Process user input
        print("\nProcessing your request...")
        start_time = time.time()
        
        with trace("NFZ Agent", group_id=conversation_id):
            input_items.append({"content": user_input, "role": "user"})
            
            # Show progress indicator for long-running operations
            progress_task = asyncio.create_task(show_progress_indicator())
            
            try:
                result = await Runner.run(current_agent, input_items)
                progress_task.cancel()
                
                # Calculate processing time
                elapsed_time = time.time() - start_time
                if elapsed_time > 1.0:
                    print(f"\nRequest processed in {elapsed_time:.1f} seconds")
                
                # Process and display results
                for new_item in result.new_items:
                    agent_name = new_item.agent.name
                    if isinstance(new_item, MessageOutputItem):
                        print(f"\n{agent_name}: {ItemHelpers.text_message_output(new_item)}")
                    elif isinstance(new_item, ToolCallItem):
                        print(f"\n{agent_name}: Calling a tool...")
                    elif isinstance(new_item, ToolCallOutputItem):
                        print(f"\n{agent_name}: Tool call completed")
                    else:
                        print(f"\n{agent_name}: Processing...")
                
                input_items = result.to_input_list()
                current_agent = result.last_agent
                
            except Exception as e:
                progress_task.cancel()
                print(f"\nError: {str(e)}")
                print("Please try again or type 'exit' to quit.")

async def show_progress_indicator():
    """Show a progress indicator during long-running operations"""
    indicators = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    
    try:
        while True:
            print(f"\r{indicators[i]} Processing...", end="", flush=True)
            i = (i + 1) % len(indicators)
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        print("\r", end="", flush=True)  # Clear the progress indicator

if __name__ == "__main__":
    asyncio.run(main())