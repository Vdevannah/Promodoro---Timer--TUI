import { useEffect, useState } from "react";
import { updateSettings } from "../api/client";

export default function SettingsPanel({ settings }) {
  const [form, setForm] = useState(settings);

  useEffect(() => {
    setForm(settings);
  }, [settings]);

  function handleChange(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleBlur(field, value) {
    if (value === settings[field]) return;
    await updateSettings({ [field]: value });
  }

  return (
    <div className="card">
      <h2>Settings</h2>
      <div className="settings-form">
        <div className="field">
          <label>Focus minutes</label>
          <input
            type="number"
            min="1"
            value={form.focus_minutes}
            onChange={(e) => handleChange("focus_minutes", Number(e.target.value))}
            onBlur={(e) => handleBlur("focus_minutes", Number(e.target.value))}
          />
        </div>
        <div className="field">
          <label>Break minutes</label>
          <input
            type="number"
            min="1"
            value={form.break_minutes}
            onChange={(e) => handleChange("break_minutes", Number(e.target.value))}
            onBlur={(e) => handleBlur("break_minutes", Number(e.target.value))}
          />
        </div>
        <div className="field">
          <label>Alarm</label>
          <select
            value={form.alarm_sound}
            onChange={(e) => {
              handleChange("alarm_sound", e.target.value);
              updateSettings({ alarm_sound: e.target.value });
            }}
          >
            <option value="bell">Bell</option>
            <option value="silent">Silent</option>
          </select>
        </div>
        <div className="field">
          <label>Background sound</label>
          <input
            type="text"
            value={form.background_sound}
            onChange={(e) => handleChange("background_sound", e.target.value)}
            onBlur={(e) => handleBlur("background_sound", e.target.value)}
          />
        </div>
      </div>
    </div>
  );
}
