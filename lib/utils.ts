/**
 * Utility functions for the application
 */

/**
 * Format a date string from the API (YYYY-MM-DD) to a human-readable format
 */
export function formatDate(dateString: string): string {
  if (!dateString) return "";

  const options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "long",
    day: "numeric",
  };

  const date = new Date(dateString);
  return date.toLocaleDateString("pl-PL", options);
}

/**
 * Calculate distance between two points using the Haversine formula
 */
export function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371; // Radius of the earth in km
  const dLat = deg2rad(lat2 - lat1);
  const dLon = deg2rad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(deg2rad(lat1)) *
      Math.cos(deg2rad(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distance = R * c; // Distance in km
  return Math.round(distance * 10) / 10;
}

function deg2rad(deg: number): number {
  return deg * (Math.PI / 180);
}

/**
 * Parse referral text to extract key information
 */
export function parseReferral(text: string): {
  benefit: string;
  keywords: string[];
} {
  // This is a simplified implementation
  // In a real application, you would use NLP or more sophisticated parsing

  // Remove common words and punctuation
  const normalizedText = text
    .toLowerCase()
    .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, " ")
    .replace(/\s{2,}/g, " ");

  // Extract keywords by removing stop words
  const stopWords = ["i", "do", "na", "w", "z", "dla", "od", "przez"];
  const words = normalizedText.split(" ");
  const keywords = words.filter(
    (word) => word.length > 2 && !stopWords.includes(word)
  );

  // Extract potential benefit names
  // This is an oversimplified approach - in real application you would
  // match against known benefit types or use more advanced NLP
  const benefitKeywords = ["poradnia", "oddział", "pracownia", "rehabilitacja"];
  let benefit = "";

  for (const keyword of benefitKeywords) {
    if (normalizedText.includes(keyword)) {
      // Find the complete phrase around the keyword
      const index = normalizedText.indexOf(keyword);
      const start = normalizedText.lastIndexOf(" ", index) + 1;
      const end = normalizedText.indexOf(" ", index + keyword.length);
      benefit = normalizedText.substring(start, end > 0 ? end : undefined);
      break;
    }
  }

  return {
    benefit,
    keywords,
  };
}

/**
 * Get user's current geolocation
 */
export function getUserLocation(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation is not supported by your browser"));
    } else {
      navigator.geolocation.getCurrentPosition(resolve, reject);
    }
  });
}
