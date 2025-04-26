from typing import Dict, List, Optional, Union, TypedDict, Any, Literal
import aiohttp
from urllib.parse import quote


# Province codes mapped to voivodeships in Poland
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

# Common benefit types
COMMON_BENEFITS = {
    "PORADNIA KARDIOLOGICZNA": "Poradnia kardiologiczna",
    "PORADNIA OKULISTYCZNA": "Poradnia okulistyczna",
    "PORADNIA NEUROLOGICZNA": "Poradnia neurologiczna",
    "PORADNIA ORTOPEDYCZNA": "Poradnia ortopedyczna",
    "PORADNIA GINEKOLOGICZNO-POŁOŻNICZA": "Poradnia ginekologiczno-położnicza",
    "PORADNIA UROLOGICZNA": "Poradnia urologiczna",
    "PORADNIA CHIRURGII OGÓLNEJ": "Poradnia chirurgii ogólnej",
    "PORADNIA OTOLARYNGOLOGICZNA": "Poradnia otolaryngologiczna",
    "PORADNIA DERMATOLOGICZNA": "Poradnia dermatologiczna",
    "PORADNIA ENDOKRYNOLOGICZNA": "Poradnia endokrynologiczna",
    "PORADNIA DIABETOLOGICZNA": "Poradnia diabetologiczna",
    "PORADNIA GASTROENTEROLOGICZNA": "Poradnia gastroenterologiczna",
    "PORADNIA REUMATOLOGICZNA": "Poradnia reumatologiczna",
    "PORADNIA PULMONOLOGICZNA": "Poradnia pulmonologiczna",
    "PORADNIA ZDROWIA PSYCHICZNEGO": "Poradnia zdrowia psychicznego",
    "ODDZIAŁ CHORÓB WEWNĘTRZNYCH": "Oddział chorób wewnętrznych",
    "ODDZIAŁ KARDIOLOGICZNY": "Oddział kardiologiczny",
    "REHABILITACJA KARDIOLOGICZNA": "Rehabilitacja kardiologiczna",
    "ODDZIAŁ CHIRURGII OGÓLNEJ": "Oddział chirurgii ogólnej",
    "ODDZIAŁ ORTOPEDYCZNY": "Oddział ortopedyczny",
    "TOMOGRAFIA KOMPUTEROWA": "Tomografia komputerowa",
    "REZONANS MAGNETYCZNY": "Rezonans magnetyczny",
    "BADANIA ENDOSKOPOWE PRZEWODU POKARMOWEGO - GASTROSKOPIA": "Gastroskopia",
    "BADANIA ENDOSKOPOWE PRZEWODU POKARMOWEGO - KOLONOSKOPIA": "Kolonoskopia",
    "PORADNIA STOMATOLOGICZNA": "Poradnia stomatologiczna",
}

# Treatment priority/case types
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
        
        return f"{url}?{'&'.join(query_params)}"
    
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
                if not response.ok:
                    error_text = await response.text()
                    raise Exception(f"NFZ API request failed: {response.status} {response.reason} - {error_text}")
                
                data = await response.json()
                
                if "errors" in data:
                    error = data["errors"][0]
                    raise Exception(f"NFZ API error: {error.get('error-reason')} - {error.get('error-solution')}")
                
                return data
        except Exception as e:
            print(f"NFZ API request failed: {e}")
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
async def find_available_visits(province: str, medical_service: str, for_children: bool = False, limit: int = 5) -> List[Queue]:
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
    # Convert province name to code if needed
    province_code = province
    if len(province) != 2:  # Not a province code
        # Find matching province code
        for code, name in PROVINCES.items():
            if name.lower() == province.lower():
                province_code = code
                break
    
    # If medical service is a common benefit key, use it directly
    if medical_service.upper() in COMMON_BENEFITS:
        benefit = medical_service.upper()
    else:
        # Try to find a matching common benefit
        benefit = None
        for key, value in COMMON_BENEFITS.items():
            if medical_service.lower() in value.lower():
                benefit = key
                break
        
        # If no match found, use the provided service name
        if not benefit:
            benefit = medical_service.upper()
    
    # Create API client
    client = NFZApiClient()
    
    # Search for available queues
    response = await client.get_queues({
        "case": 1,  # Stable case
        "province": province_code,
        "benefit": benefit,
        "benefitForChildren": for_children,
        "limit": limit,
        "format": "json"
    })
    
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