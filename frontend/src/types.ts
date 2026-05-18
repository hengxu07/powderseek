export interface TripInput {
  start_date: string; // YYYY-MM-DD
  end_date: string;
  origin_airport: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
}
