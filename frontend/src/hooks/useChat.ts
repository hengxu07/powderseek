import { useCallback, useRef, useState } from 'react';
import { ChatMessage, TripInput } from '../types';
import { apiUrl } from '../lib/api';

const TOKEN_KEY = 'powderseek_token';

// Server-issued, HMAC-signed token. Until the backend verifies the signature,
// the request 401s — so unlike the old random-UUID session_id, this can't be
// forged or replayed across sessions.
async function getToken(): Promise<string> {
  const cached = localStorage.getItem(TOKEN_KEY);
  if (cached) return cached;
  const res = await fetch(apiUrl('/session'), { method: 'POST' });
  if (!res.ok) throw new Error('Failed to create session');
  const data = await res.json();
  localStorage.setItem(TOKEN_KEY, data.token);
  return data.token;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (text: string, trip?: TripInput) => {
    if (streaming) return;

    const userMsg: ChatMessage = { role: 'user', content: text };
    const assistantMsg: ChatMessage = { role: 'assistant', content: '', streaming: true };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setStreaming(true);

    abortRef.current = new AbortController();

    try {
      const token = await getToken();
      const res = await fetch(apiUrl('/chat'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        signal: abortRef.current.signal,
        body: JSON.stringify({
          message: text,
          trip: trip ?? null,
        }),
      });

      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          let event: { type: string; content?: string };
          try {
            event = JSON.parse(raw);
          } catch {
            continue;
          }

          if (event.type === 'text' && event.content) {
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              next[next.length - 1] = { ...last, content: last.content + event.content };
              return next;
            });
          } else if (event.type === 'done') {
            break;
          } else if (event.type === 'error') {
            setMessages((prev) => {
              const next = [...prev];
              next[next.length - 1] = {
                role: 'assistant',
                content: `Something went wrong: ${event.content}`,
              };
              return next;
            });
            break;
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return;
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: 'assistant',
          content: 'Connection error — is the server running?',
        };
        return next;
      });
    } finally {
      // Mark streaming done on the last message
      setMessages((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last?.role === 'assistant') {
          next[next.length - 1] = { ...last, streaming: false };
        }
        return next;
      });
      setStreaming(false);
    }
  }, [streaming]);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setStreaming(false);
    // Drop the cached token; getToken() will mint a fresh session on next send.
    localStorage.removeItem(TOKEN_KEY);
  }, []);

  return { messages, streaming, sendMessage, reset };
}
