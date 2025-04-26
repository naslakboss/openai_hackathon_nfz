from typing import Dict, List, Optional, Union, TypedDict, Any, Literal
import aiohttp
from urllib.parse import quote
import logging
from bot_types import benefit_names, province_codes

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CaseType = Literal[1, 2]  # 1: Stable, 2: Urgent

# Type definitions for API responses
class ProviderData(TypedDict):
    awaiting: int
    removed: int
    average_period: int
    update: str

class ComputedData(TypedDict):
    average_period: int
    update: str

class QueueStatistics(TypedDict):
    provider_data: ProviderData
    computed_data: Optional[ComputedData]

class QueueDates(TypedDict):
    applicable: bool
    date: str
    date_situation_as_at: str

class BenefitsProvided(TypedDict):
    type_of_benefit: int
    year: int
    amount: int

class QueueAttributes(TypedDict):
    case: int
    benefit: str
    anesthesia: str
    many_places: str
    provider: str
    provider_code: str
    regon_provider: str
    nip_provider: str
    teryt_provider: str
    place: str
    address: str
    locality: str
    phone: str
    teryt_place: str
    registry_number: str
    id_resort_part_VII: str
    id_resort_part_VIII: str
    benefits_for_children: Optional[str]
    age_range: Optional[str]
    covid_19: str
    toilet: str
    ramp: str
    car_park: str
    elevator: str
    latitude: float
    longitude: float
    statistics: QueueStatistics
    dates: QueueDates
    benefits_provided: Optional[BenefitsProvided]

class Queue(TypedDict):
    type: str
    id: str
    attributes: QueueAttributes

class NFZMetadata(TypedDict, total=False):
    context: Optional[str]
    count: Optional[int]
    page: Optional[int]
    limit: Optional[int]
    title: Optional[str]
    url: Optional[str]
    provider: Optional[str]
    date_published: Optional[str]
    date_modified: Optional[str]
    description: Optional[str]
    keywords: Optional[str]
    language: Optional[str]
    content_type: Optional[str]
    is_part_of: Optional[str]
    message: Optional[Dict[str, str]]

class NFZLinks(TypedDict):
    first: str
    prev: Optional[str]
    self: str
    next: Optional[str]
    last: str

class QueuesResponse(TypedDict):
    meta: NFZMetadata
    links: NFZLinks
    data: List[Queue]

class QueueResponse(TypedDict):
    meta: NFZMetadata
    data: Queue

class SearchParams(TypedDict, total=False):
    page: int
    limit: int
    format: str
    api_version: str

class QueueSearchParams(SearchParams, total=False):
    case: CaseType
    province: str
    benefit: Optional[str]
    benefitForChildren: Optional[bool]
    provider: Optional[str]
    place: Optional[str]
    street: Optional[str]
    locality: Optional[str]

class VersionResponse(TypedDict):
    api_version: Dict[str, Any]


class NFZApiClient:
    """
    NFZ API Client for accessing treatment wait times in Poland
    """
    
    def __init__(self, base_url: str = "https://api.nfz.gov.pl/app-itl-api", api_version: str = "1.3"):
        """
        Initialize the NFZ API client
        
        Args:
            base_url: Base URL for the API
            api_version: API version to use
        """
        # Remove trailing slash if present
        self.base_url = base_url[:-1] if base_url.endswith("/") else base_url
        self.api_version = api_version
    
    def _build_url(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Build URL with query parameters
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Full URL with query parameters
        """
        url = f"{self.base_url}{endpoint}"
        
        # Start with API version parameter
        query_params = [f"api-version={self.api_version}"]
        
        if params:
            for key, value in params.items():
                if value is not None:
                    # Convert boolean values to lowercase strings
                    if isinstance(value, bool):
                        query_params.append(f"{key}={str(value).lower()}")
                    # URL encode string values
                    elif isinstance(value, str):
                        query_params.append(f"{key}={quote(value)}")
                    else:
                        query_params.append(f"{key}={value}")
        
        full_url = f"{url}?{'&'.join(query_params)}"
        
        return full_url
    
    async def _request(self, session: aiohttp.ClientSession, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make async API request
        
        Args:
            session: aiohttp client session
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response data
            
        Raises:
            Exception: If the API request fails
        """
        url = self._build_url(endpoint, params)
        
        try:
            async with session.get(url) as response:
                response_text = await response.text()                                
                
                if not response.ok:
                    logger.error(f"Request failed with status {response.status}: {response_text}")
                    raise Exception(f"NFZ API request failed: {response.status} {response.reason} - {response_text}")
                
                data = await response.json()
                
                if "errors" in data:
                    error = data["errors"][0]
                    error_msg = f"NFZ API error: {error.get('error-reason')} - {error.get('error-solution')}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                return data
        except Exception as e:
            logger.error(f"NFZ API request failed: {e}")
            raise
    
    async def get_queues(self, params: QueueSearchParams) -> QueuesResponse:
        """
        Get treatment wait times for specific criteria
        
        Args:
            params: Search parameters (case, province, benefit, etc.)
            
        Returns:
            List of queues with wait times
        """
        search_params = dict(params)
        # Ensure we get JSON format
        search_params["format"] = "json"
        
        logger.info(f"Searching queues with parameters: {search_params}")
        
        async with aiohttp.ClientSession() as session:
            return await self._request(session, "/queues", search_params)
    
    async def get_queue(self, queue_id: str) -> QueueResponse:
        """
        Get details for a specific queue by ID
        
        Args:
            queue_id: Queue ID
            
        Returns:
            Queue details
        """
        async with aiohttp.ClientSession() as session:
            return await self._request(session, f"/queues/{queue_id}")
    
    async def get_api_info(self) -> VersionResponse:
        """
        Get API version information
        
        Returns:
            API version details
        """
        async with aiohttp.ClientSession() as session:
            return await self._request(session, "/version")


# Helper function to find best available visits
async def find_available_visits(province: province_codes, benefit: benefit_names, locality: str, for_children: bool = False, limit: int = 5) -> List[Queue]:
    """
    Find available visits based on province and medical service
    
    Args:
        province: Province code or name
        medical_service: Medical service name
        for_children: Only show services for children
        limit: Maximum number of results to return
        
    Returns:
        List of available visits sorted by earliest date
    """
    logger.info(f"Finding visits for province: '{province}', service: '{benefit}', locality: '{locality}', for_children: {for_children}")

    client = NFZApiClient()
    
    # Prepare search parameters
    search_params = {
        "case": 1,  # Stable case
        "province": province,
        "benefit": benefit,
        "locality": locality,
        "benefitForChildren": for_children,
        "limit": limit,
        "format": "json"
    }
    
    logger.info(f"Final search parameters: {search_params}")
    
    # Search for available queues
    response = await client.get_queues(search_params)
    
    logger.info(f"Found {len(response['data'])} queues")
    
    # Return the queues data
    return response["data"]


# Helper function to format results in a human-readable way
def format_visit_results(queues: List[Queue]) -> str:
    """
    Format queue results in a human-readable way
    
    Args:
        queues: List of queues
        
    Returns:
        Formatted string with visit information
    """
    if not queues:
        return "No available visits found for the specified criteria."
    
    result = f"Found {len(queues)} available visits:\n\n"
    
    for i, queue in enumerate(queues[:5], 1):  # Limit to top 5 results
        attrs = queue["attributes"]
        date = attrs["dates"]["date"]
        provider = attrs["provider"]
        locality = attrs["locality"]
        address = attrs["address"]
        phone = attrs["phone"]
        
        result += f"{i}. {provider} in {locality}\n"
        result += f"   Address: {address}\n"
        result += f"   Phone: {phone}\n"
        result += f"   Available date: {date}\n\n"
    
    return result 


# Helper function to find province code for a locality
async def find_province_for_locality(locality: str) -> dict:
    """
    Find the province code for a given locality
    
    Args:
        locality: Name of the locality
        
    Returns:
        Dictionary with results:
        {
            "found": True/False,
            "province_code": Code if found, None if not,
            "province_name": Name if found, None if not,
            "message": Explanation message
        }
    """
    logger.info(f"Finding province for locality '{locality}'")
    
    # Default response
    result = {
        "found": False,
        "province_code": None,
        "province_name": None,
        "message": ""
    }
    
    # Mapping of province codes to names for reference
    provinces = {
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
    
    # Check if locality is too short
    if not locality or len(locality) < 3:
        result["message"] = f"Locality name too short (min 3 chars): '{locality}'"
        logger.warning(result["message"])
        return result
    
    client = NFZApiClient()
    matching_provinces = []
    
    # Check each province for the locality
    for prov_code, prov_name in provinces.items():
        try:
            # Prepare search parameters
            search_params = {
                "name": locality,
                "province": prov_code,
                "limit": 1,
                "format": "json"
            }
            
            async with aiohttp.ClientSession() as session:
                url = client._build_url("/localities", search_params)
                async with session.get(url) as response:
                    if not response.ok:
                        continue
                    
                    data = await response.json()
                    
                    if "errors" in data:
                        continue
                    
                    localities = data.get("data", [])
                    if len(localities) > 0:
                        matching_provinces.append((prov_code, prov_name))
                        logger.info(f"Found locality '{locality}' in province '{prov_code}' ({prov_name})")
        
        except Exception as e:
            logger.error(f"Error checking province {prov_code}: {e}")
    
    # Determine the result based on matches
    if len(matching_provinces) == 1:
        # Perfect match - only one province contains this locality
        prov_code, prov_name = matching_provinces[0]
        result["found"] = True
        result["province_code"] = prov_code
        result["province_name"] = prov_name
        result["message"] = f"Found locality '{locality}' in province '{prov_name}' (code: {prov_code})"
        logger.info(result["message"])
    elif len(matching_provinces) > 1:
        # Multiple matches - return all matches in message
        result["message"] = f"Locality '{locality}' found in multiple provinces: "
        result["message"] += ", ".join([f"{name} (code: {code})" for code, name in matching_provinces])
        logger.info(result["message"])
    else:
        # No matches
        result["message"] = f"Locality '{locality}' not found in any province"
        logger.warning(result["message"])
    
    return result 