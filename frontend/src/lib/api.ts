// In dev, Vite proxies /chat etc. to localhost:8000.
// In production, VITE_API_URL points to the Railway backend.
const BASE = import.meta.env.VITE_API_URL ?? '';

export const apiUrl = (path: string) => `${BASE}${path}`;
