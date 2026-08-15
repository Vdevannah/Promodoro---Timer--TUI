import { useState } from "react";
import { createTask } from "../api/client";

export default function TaskForm() {
  const [title, setTitle] = useState("");
  const [estimate, setEstimate] = useState(1);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!title.trim()) return;
    await createTask(title.trim(), Number(estimate) || 1);
    setTitle("");
    setEstimate(1);
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Add a task..."
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <input
        type="number"
        min="1"
        value={estimate}
        onChange={(e) => setEstimate(e.target.value)}
        title="Estimated pomodoros"
      />
      <button type="submit" className="btn">
        Add
      </button>
    </form>
  );
}
