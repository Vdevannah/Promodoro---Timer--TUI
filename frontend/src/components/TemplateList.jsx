import { useState } from "react";
import { createTaskFromTemplate, createTemplate, removeTemplate } from "../api/client";

export default function TemplateList({ templates }) {
  const [title, setTitle] = useState("");
  const [estimate, setEstimate] = useState(1);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!title.trim()) return;
    await createTemplate(title.trim(), Number(estimate) || 1);
    setTitle("");
    setEstimate(1);
  }

  return (
    <div className="card">
      <h2>Templates</h2>
      {templates.length === 0 ? (
        <p className="empty-note">No templates yet — save one below.</p>
      ) : (
        <div>
          {templates.map((template) => (
            <div key={template.id} className="item-row">
              <span className="item-title">{template.title}</span>
              <span className="item-meta">{template.estimate_pomodoros} pomodoros</span>
              <button
                className="btn-icon"
                onClick={() => createTaskFromTemplate(template.id)}
                title="Add as today's task"
              >
                + task
              </button>
              <button
                className="btn-icon"
                onClick={() => removeTemplate(template.id)}
                title="Remove template"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
      <form className="inline-form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Save a template..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <input
          type="number"
          min="1"
          value={estimate}
          onChange={(e) => setEstimate(e.target.value)}
          title="Default pomodoros"
        />
        <button type="submit" className="btn">
          Save
        </button>
      </form>
    </div>
  );
}
