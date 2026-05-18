import { ResortDetail, ResortSummary } from '../types';

// In dev, Vite proxies /chat etc. to localhost:8000.
// In production, VITE_API_URL points to the Railway backend.
const BASE = import.meta.env.VITE_API_URL ?? '';

export const apiUrl = (path: string) => `${BASE}${path}`;

export async function fetchResorts(): Promise<ResortSummary[]> {
  const res = await fetch(apiUrl('/resorts'));
  if (!res.ok) throw new Error('Failed to fetch resorts');
  const data = await res.json();
  return data.map((r: { name: string; slug: string }) => ({ name: r.name, slug: r.slug }));
}

export async function fetchResortDetail(slug: string): Promise<ResortDetail> {
  const res = await fetch(apiUrl(`/resort/${slug}`));
  if (!res.ok) throw new Error('Resort not found');
  return res.json();
}
