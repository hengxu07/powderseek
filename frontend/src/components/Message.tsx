import ReactMarkdown from 'react-markdown';
import { ChatMessage, ResortSummary } from '../types';
import styles from './Message.module.css';

interface Props {
  message: ChatMessage;
  resortNames?: Map<string, string>; // lowercased name → slug
  onResortClick?: (slug: string) => void;
}

export function Message({ message, resortNames, onResortClick }: Props) {
  const isUser = message.role === 'user';

  const strongRenderer = ({ children }: { children?: React.ReactNode }) => {
    const raw = typeof children === 'string' ? children
      : Array.isArray(children) ? children.map(c => (typeof c === 'string' ? c : '')).join('')
      : '';
    const slug = matchResort(raw.toLowerCase(), resortNames);
    if (slug && onResortClick) {
      return (
        <button className={styles.resortLink} onClick={() => onResortClick(slug)}>
          {children}
        </button>
      );
    }
    return <strong>{children}</strong>;
  };

  return (
    <div className={`${styles.row} ${isUser ? styles.userRow : styles.assistantRow}`}>
      {!isUser && (
        <div className={styles.avatar}>
          <SnowflakeIcon />
        </div>
      )}
      <div className={`${styles.bubble} ${isUser ? styles.userBubble : styles.assistantBubble}`}>
        {isUser ? (
          <p className={styles.userText}>{message.content}</p>
        ) : (
          <div className={styles.markdown}>
            <ReactMarkdown components={{ strong: strongRenderer }}>
              {message.content || ' '}
            </ReactMarkdown>
            {message.streaming && <span className={styles.cursor} />}
          </div>
        )}
      </div>
    </div>
  );
}

export type { ResortSummary };

// Handles bold spans like "Telluride, Colorado. This is your trip." by
// progressively stripping to find the shortest matching prefix.
function matchResort(text: string, map?: Map<string, string>): string | undefined {
  if (!map) return undefined;
  // 1. Exact match
  if (map.has(text)) return map.get(text);
  // 2. First token before comma / period / colon / exclamation
  const firstToken = text.split(/[,.!?:]/)[0]?.trim() ?? '';
  if (firstToken && map.has(firstToken)) return map.get(firstToken);
  // 3. Longest prefix word sequence within firstToken
  const words = firstToken.split(/\s+/).filter(Boolean);
  for (let len = words.length; len >= 1; len--) {
    const candidate = words.slice(0, len).join(' ');
    if (candidate.length >= 4 && map.has(candidate)) return map.get(candidate);
  }
  return undefined;
}

function SnowflakeIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="2" x2="12" y2="22" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
      <line x1="19.07" y1="4.93" x2="4.93" y2="19.07" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  );
}
