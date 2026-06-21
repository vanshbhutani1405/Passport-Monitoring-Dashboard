export const PLATFORMS = ["reddit", "youtube"];

export const CATEGORIES = [
  "passport_renewal",
  "passport_delay",
  "passport_application",
  "passport_appointment",
  "passport_verification",
  "passport_status",
  "passport_lost",
  "passport_general",
  "other",
];

export const SENTIMENTS = ["positive", "neutral", "negative", "mixed"];

export function humanize(value: string | null | undefined) {
  if (!value) return "Unknown";
  return value.replace(/_/g, " ");
}
