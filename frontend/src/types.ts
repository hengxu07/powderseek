export interface TripInput {
  start_date: string; // YYYY-MM-DD
  end_date: string;
  origin_airport: string;
  skill_level?: string;   // beginner | intermediate | advanced | expert
  budget_level?: string;  // budget | mid | premium | luxury
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
}
