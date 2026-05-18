import ReactMarkdown from 'react-markdown';
import { ChatMessage } from '../types';
import styles from './Message.module.css';

interface Props {
  message: ChatMessage;
}

export function Message({ message }: Props) {
  const isUser = message.role === 'user';

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
            <ReactMarkdown>{message.content || ' '}</ReactMarkdown>
            {message.streaming && <span className={styles.cursor} />}
          </div>
        )}
      </div>
    </div>
  );
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
