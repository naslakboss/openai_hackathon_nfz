"use client";

import { useState, useEffect } from "react";
import NFZApiClient, {
  CaseType,
  ProvinceCode,
  Queue,
  PROVINCES,
  COMMON_BENEFITS,
} from "@/lib/nfz-api";
import { formatDate, calculateDistance, parseReferral } from "@/lib/utils";

interface NFZSearchProps {
  onResultsFound?: (results: Queue[]) => void;
  apiVersion?: string;
}

export default function NFZSearch({
  onResultsFound,
  apiVersion = "1.3",
}: NFZSearchProps) {
  const [referralText, setReferralText] = useState("");
  const [selectedBenefit, setSelectedBenefit] = useState<string>("");
  const [userLocation, setUserLocation] = useState<{
    lat: number;
    lon: number;
  } | null>(null);
  const [province, setProvince] = useState<ProvinceCode>("07"); // Default to Mazowieckie
  const [results, setResults] = useState<Queue[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [customBenefit, setCustomBenefit] = useState<string>("");
  const [useCustomBenefit, setUseCustomBenefit] = useState<boolean>(false);
  const [locality, setLocality] = useState<string>("");
  const [benefitsForChildren, setBenefitsForChildren] =
    useState<boolean>(false);
  const [availableBenefits, setAvailableBenefits] = useState<string[]>([]);
  const [loadingBenefits, setLoadingBenefits] = useState(false);
  const [apiVersionInfo, setApiVersionInfo] = useState<string | null>(null);

  // Get user location
  useEffect(() => {
    const getUserCoordinates = async () => {
      try {
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            (position) => {
              setUserLocation({
                lat: position.coords.latitude,
                lon: position.coords.longitude,
              });
            },
            (err) => {
              console.error("Error getting location:", err);
              setError(
                "Nie można uzyskać lokalizacji. Proszę zezwolić na dostęp do lokalizacji."
              );
            }
          );
        }
      } catch (err) {
        console.error("Error getting location:", err);
        setError("Nie można uzyskać lokalizacji.");
      }
    };

    getUserCoordinates();
  }, []);

  // When component mounts, fetch API version info
  useEffect(() => {
    const fetchApiInfo = async () => {
      try {
        const nfzClient = new NFZApiClient(undefined, apiVersion);
        const info = await nfzClient.getApiInfo();
        setApiVersionInfo(
          `v${info["api-version"].major}.${info["api-version"].minor}.${info["api-version"].patch}`
        );
      } catch (err) {
        console.error("Error fetching API info:", err);
      }
    };

    fetchApiInfo();
  }, [apiVersion]);

  // When province changes, we might want to fetch benefits specific to that province
  useEffect(() => {
    if (province) {
      fetchBenefits();
    }
  }, [province]);

  // Fetch benefits from NFZ API
  const fetchBenefits = async (searchTerm = "poradnia") => {
    try {
      setLoadingBenefits(true);
      const nfzClient = new NFZApiClient(undefined, apiVersion);
      const response = await nfzClient.searchBenefits(searchTerm, 1, 25);
      setAvailableBenefits(response.data);
    } catch (err) {
      console.error("Error fetching benefits:", err);
    } finally {
      setLoadingBenefits(false);
    }
  };

  const handleReferralChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setReferralText(e.target.value);

    // Parse referral text to extract benefit
    if (e.target.value.length > 10) {
      const parsed = parseReferral(e.target.value);
      if (parsed.benefit) {
        // Check if the extracted benefit is one of our common benefits
        const matchedBenefit = Object.keys(COMMON_BENEFITS).find((benefitKey) =>
          benefitKey.toLowerCase().includes(parsed.benefit.toLowerCase())
        );

        if (matchedBenefit) {
          setSelectedBenefit(matchedBenefit);
          setUseCustomBenefit(false);
        } else {
          // If not found in common benefits, set as custom and fetch matching benefits
          setCustomBenefit(parsed.benefit.toUpperCase());
          setUseCustomBenefit(true);

          // We might want to prefetch benefits matching this term
          if (parsed.benefit.length >= 3) {
            fetchBenefits(parsed.benefit);
          }
        }
      }
    }
  };

  const handleProvinceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setProvince(e.target.value as ProvinceCode);
  };

  const handleBenefitChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    if (value === "custom") {
      setUseCustomBenefit(true);
    } else {
      setSelectedBenefit(value);
      setUseCustomBenefit(false);
    }
  };

  const handleCustomBenefitChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = e.target.value;
    setCustomBenefit(value);

    // We might want to prefetch benefits matching this term
    if (value.length >= 3) {
      fetchBenefits(value);
    }
  };

  const handleBenefitSelect = (benefit: string) => {
    setCustomBenefit(benefit);
  };

  const handleLocalityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocality(e.target.value);
  };

  const handleBenefitsForChildrenChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setBenefitsForChildren(e.target.checked);
  };

  const toggleCustomBenefit = () => {
    setUseCustomBenefit(!useCustomBenefit);
  };

  const searchFacilities = async () => {
    // Determine which benefit to use
    const benefitToUse = useCustomBenefit ? customBenefit : selectedBenefit;

    if (!province) {
      setError("Proszę wybrać województwo");
      return;
    }

    setLoading(true);
    setError(null);
    setSummary(null);

    try {
      const nfzClient = new NFZApiClient(undefined, apiVersion);
      const response = await nfzClient.getQueues({
        case: CaseType.STABLE,
        province,
        benefit: benefitToUse,
        benefitForChildren: benefitsForChildren,
        locality: locality || undefined,
        limit: 25,
      });

      // Process and sort results
      let facilitiesFound = response.data;

      if (facilitiesFound.length === 0) {
        setSummary("Nie znaleziono placówek dla podanych kryteriów.");
        setResults([]);
        setLoading(false);
        return;
      }

      // Sort by date (earliest first)
      facilitiesFound = facilitiesFound.sort((a, b) => {
        const dateA = a.attributes.dates.date;
        const dateB = b.attributes.dates.date;
        return new Date(dateA).getTime() - new Date(dateB).getTime();
      });

      // Add distance if user location is available
      if (userLocation) {
        facilitiesFound = facilitiesFound.map((facility) => {
          const distance = calculateDistance(
            userLocation.lat,
            userLocation.lon,
            facility.attributes.latitude,
            facility.attributes.longitude
          );

          return {
            ...facility,
            distance,
          } as Queue & { distance?: number };
        });

        // Sort by distance (closest first)
        facilitiesFound = facilitiesFound.sort((a, b) => {
          const distanceA = (a as any).distance || Infinity;
          const distanceB = (b as any).distance || Infinity;
          return distanceA - distanceB;
        });
      }

      setResults(facilitiesFound);

      // Create summary
      if (facilitiesFound.length > 0) {
        const earliestDate = formatDate(
          facilitiesFound[0].attributes.dates.date
        );
        const nearestFacility = facilitiesFound[0].attributes.provider;
        const nearestLocation = facilitiesFound[0].attributes.locality;

        setSummary(
          `Znaleziono ${facilitiesFound.length} placówek. ` +
            `Najbliższy termin: ${earliestDate} w ${nearestFacility} (${nearestLocation}).`
        );

        if (onResultsFound) {
          onResultsFound(facilitiesFound);
        }
      }
    } catch (err) {
      console.error("Error searching facilities:", err);
      setError(
        "Wystąpił błąd podczas wyszukiwania placówek. Sprawdź poprawność wprowadzonych danych."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4">
        Wyszukaj placówki dla skierowania
        {apiVersionInfo && (
          <span className="text-xs text-gray-500 ml-2">{apiVersionInfo}</span>
        )}
      </h2>

      {/* Referral input */}
      <div className="mb-4">
        <label
          htmlFor="referral"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Treść skierowania
        </label>
        <textarea
          id="referral"
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="Wklej lub przepisz treść skierowania..."
          value={referralText}
          onChange={handleReferralChange}
        />
      </div>

      {/* Search parameters */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label
            htmlFor="benefit"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Rodzaj świadczenia <span className="text-red-500">*</span>
          </label>

          {!useCustomBenefit ? (
            <div className="relative">
              <select
                id="benefit"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                value={selectedBenefit}
                onChange={handleBenefitChange}
              >
                <option value="">Wybierz rodzaj świadczenia</option>
                {Object.entries(COMMON_BENEFITS).map(([key, displayName]) => (
                  <option key={key} value={key}>
                    {displayName}
                  </option>
                ))}
                <option value="custom">Wpisz własny...</option>
              </select>

              <button
                type="button"
                onClick={toggleCustomBenefit}
                className="absolute right-2 top-2 text-xs text-blue-600 hover:text-blue-800"
              >
                Wpisz własny
              </button>
            </div>
          ) : (
            <div className="relative">
              <input
                type="text"
                id="customBenefit"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="np. PORADNIA KARDIOLOGICZNA"
                value={customBenefit}
                onChange={handleCustomBenefitChange}
              />

              <button
                type="button"
                onClick={toggleCustomBenefit}
                className="absolute right-2 top-2 text-xs text-blue-600 hover:text-blue-800"
              >
                Wybierz z listy
              </button>

              {customBenefit.length >= 3 && availableBenefits.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                  {loadingBenefits ? (
                    <div className="p-2 text-center text-sm text-gray-500">
                      Ładowanie...
                    </div>
                  ) : (
                    <ul>
                      {availableBenefits.map((benefit, index) => (
                        <li
                          key={index}
                          className="px-3 py-2 text-sm cursor-pointer hover:bg-gray-100"
                          onClick={() => handleBenefitSelect(benefit)}
                        >
                          {benefit}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          )}

          <p className="mt-1 text-xs text-gray-500">
            Wybierz z listy lub wpisz dokładną nazwę świadczenia, np. PORADNIA
            KARDIOLOGICZNA
          </p>
        </div>

        <div>
          <label
            htmlFor="province"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Województwo <span className="text-red-500">*</span>
          </label>
          <select
            id="province"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            value={province}
            onChange={handleProvinceChange}
          >
            {Object.entries(PROVINCES).map(([code, name]) => (
              <option key={code} value={code}>
                {name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Additional search parameters */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label
            htmlFor="locality"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Miejscowość
          </label>
          <input
            type="text"
            id="locality"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="np. Warszawa"
            value={locality}
            onChange={handleLocalityChange}
          />
        </div>

        <div className="flex items-center h-full pt-6">
          <input
            type="checkbox"
            id="benefitsForChildren"
            className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            checked={benefitsForChildren}
            onChange={handleBenefitsForChildrenChange}
          />
          <label
            htmlFor="benefitsForChildren"
            className="ml-2 block text-sm text-gray-700"
          >
            Tylko świadczenia dla dzieci
          </label>
        </div>
      </div>

      {/* Search button */}
      <div className="mb-6">
        <button
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
          onClick={searchFacilities}
          disabled={loading}
        >
          {loading ? "Wyszukiwanie..." : "Wyszukaj placówki"}
        </button>
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md">
          {error}
        </div>
      )}

      {/* Summary */}
      {summary && (
        <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-md">
          {summary}
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="border rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Placówka
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Lokalizacja
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Najbliższy termin
                </th>
                {userLocation && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Odległość
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {results.map((facility) => (
                <tr key={facility.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {facility.attributes.provider}
                    </div>
                    <div className="text-sm text-gray-500">
                      {facility.attributes.place}
                    </div>
                    <div className="text-sm text-gray-500">
                      {facility.attributes.phone}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {facility.attributes.locality}
                    </div>
                    <div className="text-sm text-gray-500">
                      {facility.attributes.address}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {formatDate(facility.attributes.dates.date)}
                    </div>
                  </td>
                  {userLocation && (
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {(facility as any).distance !== undefined
                          ? `${(facility as any).distance} km`
                          : "Brak danych"}
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
