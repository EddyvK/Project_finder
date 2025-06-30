/**
 * Date utility functions for handling European date format (DD.MM.YYYY)
 */

/**
 * Validates if a string is in European date format (DD.MM.YYYY)
 */
export const isValidEuropeanDate = (dateString: string): boolean => {
  if (!dateString) return false;

  const europeanDatePattern = /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/;
  const match = dateString.match(europeanDatePattern);

  if (!match) return false;

  const [, day, month, year] = match;
  const dayNum = parseInt(day, 10);
  const monthNum = parseInt(month, 10);
  const yearNum = parseInt(year, 10);

  // Basic validation
  if (yearNum < 1900 || yearNum > 2100) return false;
  if (monthNum < 1 || monthNum > 12) return false;
  if (dayNum < 1 || dayNum > 31) return false;

  // Check for valid days in month
  const daysInMonth = new Date(yearNum, monthNum, 0).getDate();
  return dayNum <= daysInMonth;
};

/**
 * Converts European date format (DD.MM.YYYY) to ISO date format (YYYY-MM-DD)
 */
export const europeanToIsoDate = (dateString: string): string | null => {
  if (!isValidEuropeanDate(dateString)) return null;

  const europeanDatePattern = /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/;
  const match = dateString.match(europeanDatePattern);

  if (!match) return null;

  const [, day, month, year] = match;
  return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
};

/**
 * Converts ISO date format (YYYY-MM-DD) to European date format (DD.MM.YYYY)
 */
export const isoToEuropeanDate = (isoDate: string): string | null => {
  if (!isoDate) return null;

  try {
    const date = new Date(isoDate);
    if (isNaN(date.getTime())) return null;

    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();

    return `${day}.${month}.${year}`;
  } catch {
    return null;
  }
};

/**
 * Formats a date string for display, handling both European and ISO formats
 */
export const formatDateForDisplay = (dateString: string | undefined): string => {
  if (!dateString) return 'N/A';

  // Handle European date format (DD.MM.YYYY)
  if (isValidEuropeanDate(dateString)) {
    const isoDate = europeanToIsoDate(dateString);
    if (isoDate) {
      return new Date(isoDate).toLocaleDateString('de-DE');
    }
  }

  // Fallback: try to parse as ISO date or return as-is
  try {
    return new Date(dateString).toLocaleDateString('de-DE');
  } catch {
    return dateString; // Return original string if parsing fails
  }
};

/**
 * Gets the current date in European format
 */
export const getCurrentDateEuropean = (): string => {
  const now = new Date();
  const day = now.getDate().toString().padStart(2, '0');
  const month = (now.getMonth() + 1).toString().padStart(2, '0');
  const year = now.getFullYear();

  return `${day}.${month}.${year}`;
};

/**
 * Compares two dates in European format
 * Returns: -1 if date1 < date2, 0 if equal, 1 if date1 > date2
 */
export const compareEuropeanDates = (date1: string, date2: string): number => {
  const iso1 = europeanToIsoDate(date1);
  const iso2 = europeanToIsoDate(date2);

  if (!iso1 || !iso2) return 0;

  const d1 = new Date(iso1);
  const d2 = new Date(iso2);

  if (d1 < d2) return -1;
  if (d1 > d2) return 1;
  return 0;
};