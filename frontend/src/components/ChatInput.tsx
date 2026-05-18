import { KeyboardEvent, useRef, useState } from 'react';
import { TripInput as TripInputType } from '../types';
import { TripInput } from './TripInput';
import styles from './ChatInput.module.css';

interface Props {
  onSend: (text: string, trip?: TripInputType) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState('');
  const [trip, setTrip] = useState<TripInputType | undefined>();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function submit() {
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text, trip);
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function onInput() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  }

  return (
    <div className={styles.root}>
      <div className={styles.inputBox}>
        <div className={styles.toolbar}>
          <TripInput onSet={setTrip} />
        </div>
        <div className={styles.inputRow}>
          <textarea
            ref={textareaRef}
            className={styles.textarea}
            placeholder="Where should I ski this weekend?"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKeyDown}
            onInput={onInput}
            disabled={disabled}
            rows={1}
          />
          <button
            className={styles.send}
            onClick={submit}
            disabled={disabled || !value.trim()}
            aria-label="Send"
          >
            {disabled ? <SpinnerIcon /> : <SendIcon />}
          </button>
        </div>
      </div>
      <p className={styles.hint}>Enter to send · Shift+Enter for newline</p>
    </div>
  );
}

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

function SpinnerIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ animation: 'spin 1s linear infinite' }}>
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}
