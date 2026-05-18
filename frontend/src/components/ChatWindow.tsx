import { useCallback, useEffect, useRef, useState } from 'react';
import { TripInput as TripInputType } from '../types';
import { fetchResorts } from '../lib/api';
import { useChat } from '../hooks/useChat';
import { Message } from './Message';
import { ChatInput } from './ChatInput';
import { ResortDrawer } from './ResortDrawer';
import styles from './ChatWindow.module.css';

const SUGGESTIONS = [
  "Where should I ski this weekend?",
  "I have 5 days in February — where's the best powder right now?",
  "Surprise me — 10 days, open to flying anywhere.",
  "Best resorts for advanced skiers within a day trip of Orange County?",
];

export function ChatWindow() {
  const { messages, streaming, sendMessage, reset } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const [resortNames, setResortNames] = useState<Map<string, string>>(new Map());
  const [drawerSlug, setDrawerSlug] = useState<string | null>(null);

  // Load resort name → slug map once on mount, with normalized variants for fuzzy matching
  useEffect(() => {
    fetchResorts().then(list => {
      const map = new Map<string, string>();
      for (const r of list) {
        const lower = r.name.toLowerCase();
        map.set(lower, r.slug);
        // Normalize spaces around slashes: "val d'isère / tignes" → "val d'isère/tignes"
        const compact = lower.replace(/\s*\/\s*/g, '/');
        map.set(compact, r.slug);
        // Add first component as alias: "val d'isère" → val-disere
        const first = lower.split(/\s*\/\s*/)[0].trim();
        if (first && first !== lower) map.set(first, r.slug);
      }
      setResortNames(map);
    }).catch(() => {});
  }, []);

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function handleSend(text: string, trip?: TripInputType) {
    sendMessage(text, trip);
  }

  const closeDrawer = useCallback(() => setDrawerSlug(null), []);

  const isEmpty = messages.length === 0;

  return (
    <div className={`${styles.root} ${drawerSlug ? styles.rootDrawerOpen : ''}`}>
      {/* Message list */}
      <div className={styles.list} ref={listRef}>
        {isEmpty ? (
          <div className={styles.empty}>
            <div className={styles.emptyIcon}>🏔️</div>
            <h2 className={styles.emptyTitle}>Where to next?</h2>
            <p className={styles.emptySubtitle}>
              Tell me how many days you have and I'll find you the best powder.
            </p>
            <div className={styles.suggestions}>
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  className={styles.suggestion}
                  onClick={() => handleSend(s)}
                  type="button"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className={styles.messages}>
            {messages.map((msg, i) => (
              <Message
                key={i}
                message={msg}
                resortNames={resortNames}
                onResortClick={setDrawerSlug}
              />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={streaming} />

      {/* Reset button (only when there are messages) */}
      {!isEmpty && (
        <button className={styles.reset} onClick={reset} type="button" title="Start a new chat">
          New chat
        </button>
      )}

      {/* Resort detail drawer */}
      <ResortDrawer slug={drawerSlug} onClose={closeDrawer} />
    </div>
  );
}
