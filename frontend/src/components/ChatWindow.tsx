import { useEffect, useRef } from 'react';
import { TripInput as TripInputType } from '../types';
import { useChat } from '../hooks/useChat';
import { Message } from './Message';
import { ChatInput } from './ChatInput';
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

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function handleSend(text: string, trip?: TripInputType) {
    sendMessage(text, trip);
  }

  const isEmpty = messages.length === 0;

  return (
    <div className={styles.root}>
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
              <Message key={i} message={msg} />
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
    </div>
  );
}
