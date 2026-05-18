export interface TripInput {
  start_date: string; // YYYY-MM-DD
  end_date: string;
  origin_airport: string;
  skill_level?: string;   // beginner | intermediate | advanced | expert
  budget_level?: string;  // budget | mid | premium | luxury
}

export interface ForecastDay {
  forecast_date: string;
  new_snow_cm: number | null;
  cumulative_7d_cm: number | null;
  base_depth_cm: number | null;
  temperature_c: number | null;
  wind_kph: number | null;
}

export interface ResortDetail {
  id: number;
  name: string;
  slug: string;
  country: string;
  continent: string;
  region: string | null;
  lat: number;
  lon: number;
  elevation_base_m: number;
  elevation_summit_m: number;
  vertical_drop_m: number;
  nearest_airport: string;
  airport_drive_minutes: number;
  season_start_month: number;
  season_end_month: number;
  avg_annual_snowfall_cm: number | null;
  difficulty_mix: Record<string, number> | null;
  terrain_tags: string[];
  vibe_tags: string[];
  budget_tier: string | null;
  agent_notes: string | null;
  forecast_days: ForecastDay[];
}

export interface ResortSummary {
  name: string;
  slug: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
}
