import { useEffect, useState } from "react";
import { getReport } from "../api/client";

const GRANULARITIES = ["day", "week", "month"];

export default function ReportPanel() {
  const [granularity, setGranularity] = useState("day");
  const [rows, setRows] = useState([]);

  useEffect(() => {
    let cancelled = false;
    getReport(granularity).then((data) => {
      if (!cancelled) setRows(data);
    });
    return () => {
      cancelled = true;
    };
  }, [granularity]);

  const maxSessions = Math.max(1, ...rows.map((r) => r.sessions));
  const recentFirst = [...rows].reverse();

  return (
    <div className="card">
      <h2>Focus time</h2>
      <div className="report-toggle">
        {GRANULARITIES.map((g) => (
          <button
            key={g}
            className={g === granularity ? "active" : ""}
            onClick={() => setGranularity(g)}
          >
            {g}
          </button>
        ))}
      </div>
      {rows.length === 0 ? (
        <p className="empty-note">No focus sessions recorded yet.</p>
      ) : (
        <div className="bar-chart">
          {recentFirst.map((row) => (
            <div className="bar-row" key={row.label}>
              <span className="bar-label">{row.label}</span>
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{ width: `${(row.sessions / maxSessions) * 100}%` }}
                  title={`${row.sessions} sessions · ${row.minutes}m`}
                />
              </div>
              <span className="bar-value">
                {row.sessions} · {row.minutes}m
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
