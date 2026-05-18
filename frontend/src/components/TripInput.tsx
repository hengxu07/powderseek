import { useState } from 'react';
import { TripInput as TripInputType } from '../types';
import styles from './TripInput.module.css';

interface Props {
  onSet: (trip: TripInputType | undefined) => void;
}

export function TripInput({ onSet }: Props) {
  const [open, setOpen] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [airport, setAirport] = useState('SNA');
  const [active, setActive] = useState(false);

  const today = new Date().toISOString().split('T')[0];

  const durationDays =
    startDate && endDate
      ? Math.max(
          1,
          Math.round(
            (new Date(endDate).getTime() - new Date(startDate).getTime()) /
              86_400_000 +
              1
          )
        )
      : null;

  function apply() {
    if (!startDate || !endDate) return;
    onSet({ start_date: startDate, end_date: endDate, origin_airport: airport || 'SNA' });
    setActive(true);
    setOpen(false);
  }

  function clear() {
    setStartDate('');
    setEndDate('');
    setAirport('SNA');
    setActive(false);
    onSet(undefined);
  }

  return (
    <div className={styles.root}>
      <button
        className={`${styles.toggle} ${active ? styles.toggleActive : ''}`}
        onClick={() => setOpen((o) => !o)}
        type="button"
      >
        <CalendarIcon />
        {active && durationDays
          ? `${startDate} → ${endDate} · ${durationDays}d · ${airport}`
          : 'Plan a trip'}
        {active && (
          <span
            className={styles.clear}
            onClick={(e) => { e.stopPropagation(); clear(); }}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && clear()}
          >
            ✕
          </span>
        )}
      </button>

      {open && (
        <div className={styles.panel}>
          <div className={styles.fields}>
            <label className={styles.field}>
              <span>From</span>
              <input
                type="date"
                min={today}
                value={startDate}
                onChange={(e) => {
                  setStartDate(e.target.value);
                  if (endDate && e.target.value > endDate) setEndDate('');
                }}
              />
            </label>
            <label className={styles.field}>
              <span>To</span>
              <input
                type="date"
                min={startDate || today}
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </label>
            <label className={styles.field}>
              <span>Flying from</span>
              <input
                type="text"
                maxLength={3}
                placeholder="SNA"
                value={airport}
                onChange={(e) => setAirport(e.target.value.toUpperCase())}
              />
            </label>
          </div>

          {durationDays && (
            <p className={styles.duration}>
              {durationDays} day{durationDays !== 1 ? 's' : ''} —{' '}
              {durationDays === 1
                ? 'day trip'
                : durationDays <= 3
                ? 'weekend'
                : durationDays <= 5
                ? 'short trip'
                : durationDays <= 7
                ? 'medium trip'
                : durationDays <= 14
                ? 'long trip — international resorts unlocked 🌏'
                : 'expedition — anywhere on the planet 🗺️'}
            </p>
          )}

          <div className={styles.actions}>
            <button className={styles.cancel} onClick={() => setOpen(false)} type="button">
              Cancel
            </button>
            <button
              className={styles.apply}
              onClick={apply}
              disabled={!startDate || !endDate}
              type="button"
            >
              Set trip
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function CalendarIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  );
}
