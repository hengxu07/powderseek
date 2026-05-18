import { ChatWindow } from './components/ChatWindow';
import styles from './App.module.css';

export function App() {
  return (
    <div className={styles.root}>
      <header className={styles.header}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>❄️</span>
          <span className={styles.logoText}>Powderseek</span>
        </div>
        <p className={styles.tagline}>AI-powered ski trip planner</p>
      </header>
      <main className={styles.main}>
        <ChatWindow />
      </main>
    </div>
  );
}
