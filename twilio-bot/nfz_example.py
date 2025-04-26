#!/usr/bin/env python3
"""
Example script demonstrating the use of the NFZ API client.

Usage:
    python nfz_example.py [province] [service]

Example:
    python nfz_example.py "06" "PORADNIA OKULISTYCZNA"
    python nfz_example.py krakow ophthalmology
"""

import asyncio
import sys
import json
from nfz_api import find_available_visits, format_visit_results


async def main():
    """
    Main function that demonstrates the use of the NFZ API client.
    """
    # Parse command line arguments or use defaults
    province = sys.argv[1] if len(sys.argv) > 1 else "07"  # Default to Mazowieckie
    service = sys.argv[2] if len(sys.argv) > 2 else "PORADNIA OKULISTYCZNA"
    
    print(f"Searching for '{service}' visits in province '{province}'...")
    
    try:
        # Query the NFZ API
        queues = await find_available_visits(
            province=province,
            benefit=service,
            for_children=False,
            limit=5
        )
        
        # Print full JSON response for debugging
        # print("\nRaw JSON response (first queue only):")
        # if queues:
        #     print(json.dumps(queues[0], indent=2, ensure_ascii=False)[:1000] + "...(truncated)")
        # else:
        #     print("No queues found")
        
        # Format and print the results in a human-readable way
        # print("\nFormatted results:")
        formatted_results = format_visit_results(queues)
        # print(formatted_results)
        
    except Exception as e:
        print(f"Error: {e}")
        

if __name__ == "__main__":
    asyncio.run(main()) 