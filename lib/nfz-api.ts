/**
 * NFZ API Client
 * API documentation: https://api.nfz.gov.pl/app-itl-api/
 */

// Province codes mapped to voivodeships in Poland
export const PROVINCES = {
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
} as const;

export type ProvinceCode = keyof typeof PROVINCES;

// Common benefit types
export const COMMON_BENEFITS = {
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
} as const;

export type BenefitType = keyof typeof COMMON_BENEFITS;

// Treatment priority/case types
export enum CaseType {
  STABLE = 1, // Stabilny (Stable)
  URGENT = 2, // Pilny (Urgent)
}

// Response types from NFZ API
export interface NFZMetadata {
  context?: string;
  count?: number;
  page?: number;
  limit?: number;
  title?: string;
  url?: string | null;
  provider?: string;
  "date-published"?: string;
  "date-modified"?: string;
  description?: string;
  keywords?: string;
  language?: string;
  "content-type"?: string;
  "is-part-of"?: string;
  message?: {
    type: string;
    content: string;
  } | null;
}

export interface NFZLinks {
  first: string;
  prev: string | null;
  self: string;
  next: string | null;
  last: string;
}

export interface NFZError {
  id: string;
  "error-result": string;
  "error-reason": string;
  "error-solution": string;
  "error-help": string;
  "error-code": number;
}

export interface NFZErrorResponse {
  errors: NFZError[];
}

// Queue types
export interface ProviderData {
  awaiting: number;
  removed: number;
  "average-period": number;
  update: string;
}

export interface ComputedData {
  "average-period": number;
  update: string;
}

export interface QueueStatistics {
  "provider-data": ProviderData;
  "computed-data": ComputedData | null;
}

export interface QueueDates {
  applicable: boolean;
  date: string;
  "date-situation-as-at": string;
}

export interface BenefitsProvided {
  "type-of-benefit": number;
  year: number;
  amount: number;
}

export interface QueueAttributes {
  case: number;
  benefit: string;
  anesthesia: string;
  "many-places": string;
  provider: string;
  "provider-code": string;
  "regon-provider": string;
  "nip-provider": string;
  "teryt-provider": string;
  place: string;
  address: string;
  locality: string;
  phone: string;
  "teryt-place": string;
  "registry-number": string;
  "id-resort-part-VII": string;
  "id-resort-part-VIII": string;
  "benefits-for-children": string | null;
  "age-range": string | null;
  "covid-19": string;
  toilet: string;
  ramp: string;
  "car-park": string;
  elevator: string;
  latitude: number;
  longitude: number;
  statistics: QueueStatistics;
  dates: QueueDates;
  "benefits-provided": BenefitsProvided | null;
}

export interface Queue {
  type: string;
  id: string;
  attributes: QueueAttributes;
}

export interface QueuesResponse {
  meta: NFZMetadata;
  links: NFZLinks;
  data: Queue[];
}

export interface QueueResponse {
  meta: NFZMetadata;
  data: Queue;
}

export interface ManyPlacesAttributes {
  benefit: string;
  provider: string;
  places: Array<{
    id: string;
    type: string;
    attributes: {
      place: string;
      address: string;
      locality: string;
      phone: string;
      "teryt-place": string;
      "id-resort-part-VII": string;
      "id-resort-part-VIII": string;
      "benefits-for-children": string;
      "age-range": string;
      anesthesia: string;
      "covid-19": string;
      toilet: string;
      ramp: string;
      "car-park": string;
      elevator: string;
      latitude: number;
      longitude: number;
      statistics: QueueStatistics;
      dates: QueueDates;
    };
  }>;
}

export interface ManyPlacesResponse {
  meta: NFZMetadata;
  data: {
    type: string;
    attributes: ManyPlacesAttributes;
  };
}

export interface BenefitsResponse {
  meta: NFZMetadata;
  links: NFZLinks;
  data: string[];
}

export interface LocalitiesResponse {
  meta: NFZMetadata;
  links: NFZLinks;
  data: string[];
}

export interface PlacesResponse {
  meta: NFZMetadata;
  links: NFZLinks;
  data: string[];
}

export interface ProvidersResponse {
  meta: NFZMetadata;
  links: NFZLinks;
  data: string[];
}

export interface StreetsResponse {
  meta: NFZMetadata;
  links: NFZLinks;
  data: string[];
}

export interface VersionResponse {
  "api-version": {
    major: number;
    minor: number;
    patch: number;
    "date-mod": string;
    deprecated: boolean;
  };
}

// Request parameters
export interface SearchParams {
  page?: number;
  limit?: number;
  format?: string;
  "api-version"?: string;
  [key: string]: any;
}

export interface QueueSearchParams extends SearchParams {
  case: CaseType;
  province: ProvinceCode;
  benefit?: string;
  benefitForChildren?: boolean;
  provider?: string;
  place?: string;
  street?: string;
  locality?: string;
}

export interface BenefitSearchParams extends SearchParams {
  name: string; // Minimum 3 characters
}

export interface LocalitySearchParams extends SearchParams {
  name: string; // Minimum 3 characters
  province?: ProvinceCode;
}

export interface PlaceSearchParams extends SearchParams {
  name: string; // Minimum 3 characters
  province?: ProvinceCode;
}

export interface ProviderSearchParams extends SearchParams {
  name: string; // Minimum 3 characters
  province?: ProvinceCode;
}

export interface StreetSearchParams extends SearchParams {
  name: string; // Minimum 3 characters
  province?: ProvinceCode;
}

/**
 * NFZ API Client for accessing treatment wait times
 */
export class NFZApiClient {
  private readonly baseUrl: string;
  private readonly apiVersion: string;

  constructor(
    baseUrl = "https://api.nfz.gov.pl/app-itl-api",
    apiVersion = "1.3"
  ) {
    // Remove trailing slash if present
    this.baseUrl = baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;
    this.apiVersion = apiVersion;
  }

  /**
   * Build URL with query parameters
   */
  private buildUrl(endpoint: string, params?: SearchParams): string {
    const url = new URL(`${this.baseUrl}${endpoint}`);

    // Add API version by default
    url.searchParams.append("api-version", this.apiVersion);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.append(key, value.toString());
        }
      });
    }

    return url.toString();
  }

  /**
   * Make API request
   */
  private async request<T>(
    endpoint: string,
    params?: SearchParams
  ): Promise<T> {
    const url = this.buildUrl(endpoint, params);

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(
          `NFZ API request failed: ${response.status} ${response.statusText}`
        );
      }

      const data = await response.json();

      if ("errors" in data) {
        throw new Error(
          `NFZ API error: ${data.errors[0]["error-reason"]} - ${data.errors[0]["error-solution"]}`
        );
      }

      return data as T;
    } catch (error) {
      console.error("NFZ API request failed:", error);
      throw error;
    }
  }

  /**
   * Get treatment wait times for specific criteria
   *
   * @param params Search parameters (case, province, benefit, etc.)
   * @returns List of queues with wait times
   */
  async getQueues(params: QueueSearchParams): Promise<QueuesResponse> {
    return this.request<QueuesResponse>("/queues", {
      ...params,
      format: "json",
    });
  }

  /**
   * Get details for a specific queue by ID
   *
   * @param id Queue ID
   * @returns Queue details
   */
  async getQueue(id: string): Promise<QueueResponse> {
    return this.request<QueueResponse>(`/queues/${id}`);
  }

  /**
   * Get details for other places providing the same service
   *
   * @param id Queue ID with many-places=Y
   * @returns List of places providing the same service
   */
  async getManyPlaces(id: string): Promise<ManyPlacesResponse> {
    return this.request<ManyPlacesResponse>(`/many-places/${id}`);
  }

  /**
   * Search for available medical benefits/procedures
   *
   * @param name Benefit name to search (minimum 3 characters)
   * @param page Page number (starting from 1)
   * @param limit Number of results per page
   * @returns List of benefits/procedures
   */
  async searchBenefits(
    name: string,
    page = 1,
    limit = 10
  ): Promise<BenefitsResponse> {
    return this.request<BenefitsResponse>("/benefits", {
      name,
      page,
      limit,
      format: "json",
    });
  }

  /**
   * Search for localities where services are available
   *
   * @param name Locality name to search (minimum 3 characters)
   * @param province Optional province code to filter by
   * @param page Page number (starting from 1)
   * @param limit Number of results per page
   * @returns List of localities
   */
  async searchLocalities(
    name: string,
    province?: ProvinceCode,
    page = 1,
    limit = 10
  ): Promise<LocalitiesResponse> {
    return this.request<LocalitiesResponse>("/localities", {
      name,
      province,
      page,
      limit,
      format: "json",
    });
  }

  /**
   * Search for places where services are provided
   *
   * @param name Place name to search (minimum 3 characters)
   * @param province Optional province code to filter by
   * @param page Page number (starting from 1)
   * @param limit Number of results per page
   * @returns List of places
   */
  async searchPlaces(
    name: string,
    province?: ProvinceCode,
    page = 1,
    limit = 10
  ): Promise<PlacesResponse> {
    return this.request<PlacesResponse>("/places", {
      name,
      province,
      page,
      limit,
      format: "json",
    });
  }

  /**
   * Search for healthcare providers
   *
   * @param name Provider name to search (minimum 3 characters)
   * @param province Optional province code to filter by
   * @param page Page number (starting from 1)
   * @param limit Number of results per page
   * @returns List of providers
   */
  async searchProviders(
    name: string,
    province?: ProvinceCode,
    page = 1,
    limit = 10
  ): Promise<ProvidersResponse> {
    return this.request<ProvidersResponse>("/providers", {
      name,
      province,
      page,
      limit,
      format: "json",
    });
  }

  /**
   * Search for streets where services are provided
   *
   * @param name Street name to search (minimum 3 characters)
   * @param province Optional province code to filter by
   * @param page Page number (starting from 1)
   * @param limit Number of results per page
   * @returns List of streets
   */
  async searchStreets(
    name: string,
    province?: ProvinceCode,
    page = 1,
    limit = 10
  ): Promise<StreetsResponse> {
    return this.request<StreetsResponse>("/streets", {
      name,
      province,
      page,
      limit,
      format: "json",
    });
  }

  /**
   * Get API version information
   */
  async getApiInfo(): Promise<VersionResponse> {
    return this.request("/version");
  }
}

export default NFZApiClient;
