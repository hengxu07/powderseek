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
    const text = typeof children === 'string' ? children
      : Array.isArray(children) ? children.map(c => (typeof c === 'string' ? c : '')).join('')
      : '';
    const slug = resortNames?.get(text.toLowerCase());
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
