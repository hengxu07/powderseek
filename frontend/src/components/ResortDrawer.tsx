import { useEffect, useRef, useState } from 'react';
import { ResortDetail } from '../types';
import { fetchResortDetail } from '../lib/api';
import styles from './ResortDrawer.module.css';

interface Props {
  slug: string | null;
  onClose: () => void;
}

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const BUDGET_LABELS: Record<string, string> = {
  budget: 'Budget-friendly',
  mid: 'Mid-range',
  premium: 'Premium',
  luxury: 'Luxury',
};
const DIFFICULTY_COLORS: Record<string, string> = {
  beginner: '#4caf50',
  intermediate: '#2196f3',
  advanced: '#212121',
  expert: '#f44336',
};
const DIFFICULTY_ORDER = ['beginner', 'intermediate', 'advanced', 'expert'];

export function ResortDrawer({ slug, onClose }: Props) {
  const [resort, setResort] = useState<ResortDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const drawerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!slug) { setResort(null); return; }
    setLoading(true);
    fetchResortDetail(slug)
      .then(setResort)
      .catch(() => setResort(null))
      .finally(() => setLoading(false));
  }, [slug]);

  // Close on Escape
  useEffect(() => {
    if (!slug) return;
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') onClose(); }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [slug, onClose]);

  const open = !!slug;

  const snowDays = resort?.forecast_days ?? [];
  const maxSnow = Math.max(...snowDays.map(d => d.new_snow_cm ?? 0), 1);

  const diffMix = resort?.difficulty_mix ?? {};
  const diffTotal = DIFFICULTY_ORDER.reduce((s, k) => s + (diffMix[k] ?? 0), 0);

  const todaySnow = snowDays[0];

  return (
    <>
      {/* Backdrop */}
      <div
        className={`${styles.backdrop} ${open ? styles.backdropOpen : ''}`}
        onClick={onClose}
        aria-hidden
      />

      {/* Drawer */}
      <div
        ref={drawerRef}
        className={`${styles.drawer} ${open ? styles.drawerOpen : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label="Resort detail"
      >
        {loading && (
          <div className={styles.loading}>Loading…</div>
        )}

        {!loading && resort && (
          <div className={styles.content}>
            {/* Header */}
            <div className={styles.header}>
              <div>
                <h2 className={styles.name}>{resort.name}</h2>
                <p className={styles.location}>
                  {resort.country} · {resort.continent.replace('_', ' ')}
                  {resort.region ? ` · ${resort.region}` : ''}
                </p>
              </div>
              <button className={styles.close} onClick={onClose} aria-label="Close">✕</button>
            </div>

            {/* Ski-only warning */}
            {!resort.snowboard_allowed && (
              <div className={styles.skiOnlyBanner}>
                ⛷ Ski only — snowboarding not permitted
              </div>
            )}

            {/* Snow snapshot */}
            <section className={styles.section}>
              <h3 className={styles.sectionLabel}>Snow Conditions</h3>
              <div className={styles.statsRow}>
                <Stat label="New snow" value={todaySnow?.new_snow_cm != null ? `${todaySnow.new_snow_cm} cm` : '—'} />
                <Stat label="7-day total" value={todaySnow?.cumulative_7d_cm != null ? `${todaySnow.cumulative_7d_cm} cm` : '—'} />
                <Stat label="Base depth" value={todaySnow?.base_depth_cm != null ? `${todaySnow.base_depth_cm} cm` : '—'} />
              </div>
            </section>

            {/* 7-day bar chart */}
            {snowDays.length > 0 && (
              <section className={styles.section}>
                <h3 className={styles.sectionLabel}>7-Day Forecast</h3>
                <div className={styles.chart}>
                  {snowDays.map((day) => {
                    const cm = day.new_snow_cm ?? 0;
                    const pct = (cm / maxSnow) * 100;
                    const label = new Date(day.forecast_date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short' });
                    return (
                      <div key={day.forecast_date} className={styles.chartCol}>
                        <span className={styles.chartVal}>{cm > 0 ? `${Math.round(cm)}` : ''}</span>
                        <div className={styles.barWrap}>
                          <div className={styles.bar} style={{ height: `${Math.max(pct, 2)}%` }} />
                        </div>
                        <span className={styles.chartDay}>{label}</span>
                      </div>
                    );
                  })}
                </div>
                <p className={styles.chartUnit}>cm / day</p>
              </section>
            )}

            {/* Terrain breakdown */}
            {diffTotal > 0 && (
              <section className={styles.section}>
                <h3 className={styles.sectionLabel}>Terrain Breakdown</h3>
                <div className={styles.diffStack}>
                  {DIFFICULTY_ORDER.filter(k => diffMix[k] > 0).map(k => (
                    <div
                      key={k}
                      className={styles.diffSegment}
                      style={{ width: `${(diffMix[k] / diffTotal) * 100}%`, background: DIFFICULTY_COLORS[k] }}
                      title={`${k} ${diffMix[k]}%`}
                    />
                  ))}
                </div>
                <div className={styles.diffLegend}>
                  {DIFFICULTY_ORDER.filter(k => diffMix[k] > 0).map(k => (
                    <span key={k} className={styles.diffLegendItem}>
                      <span className={styles.diffDot} style={{ background: DIFFICULTY_COLORS[k] }} />
                      {k.charAt(0).toUpperCase() + k.slice(1)} {diffMix[k]}%
                    </span>
                  ))}
                </div>
              </section>
            )}

            {/* Mountain stats */}
            <section className={styles.section}>
              <h3 className={styles.sectionLabel}>Mountain</h3>
              <div className={styles.detailGrid}>
                <DetailRow label="Vertical drop" value={`${resort.vertical_drop_m} m`} />
                <DetailRow label="Base elevation" value={`${resort.elevation_base_m} m`} />
                <DetailRow label="Summit" value={`${resort.elevation_summit_m} m`} />
                <DetailRow label="Season" value={`${MONTHS[resort.season_start_month - 1]} – ${MONTHS[resort.season_end_month - 1]}`} />
                {resort.avg_annual_snowfall_cm && (
                  <DetailRow label="Avg snowfall" value={`${resort.avg_annual_snowfall_cm} cm/yr`} />
                )}
                {resort.budget_tier && (
                  <DetailRow label="Budget" value={BUDGET_LABELS[resort.budget_tier] ?? resort.budget_tier} />
                )}
                <DetailRow label="Nearest airport" value={`${resort.nearest_airport} (${resort.airport_drive_minutes} min drive)`} />
              </div>
            </section>

            {/* Tags */}
            {resort.terrain_tags.length > 0 && (
              <section className={styles.section}>
                <h3 className={styles.sectionLabel}>Terrain</h3>
                <div className={styles.tags}>
                  {resort.terrain_tags.map(t => <span key={t} className={styles.tag}>{t}</span>)}
                </div>
              </section>
            )}

            {resort.vibe_tags.length > 0 && (
              <section className={styles.section}>
                <h3 className={styles.sectionLabel}>Vibe</h3>
                <div className={styles.tags}>
                  {resort.vibe_tags.map(t => <span key={t} className={styles.tag}>{t}</span>)}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.stat}>
      <span className={styles.statValue}>{value}</span>
      <span className={styles.statLabel}>{label}</span>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <>
      <span className={styles.detailLabel}>{label}</span>
      <span className={styles.detailValue}>{value}</span>
    </>
  );
}
