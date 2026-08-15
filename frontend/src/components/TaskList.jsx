import { completeTask, removeTask, selectTask } from "../api/client";
import TaskForm from "./TaskForm";

export default function TaskList({ tasks, selectedTaskId }) {
  return (
    <div className="card">
      <h2>Tasks</h2>
      {tasks.length === 0 ? (
        <p className="empty-note">No tasks yet — add one below.</p>
      ) : (
        <div>
          {tasks.map((task) => (
            <div
              key={task.id}
              className={`item-row${task.id === selectedTaskId ? " selected" : ""}`}
            >
              <span
                className={`item-title${task.status === "done" ? " done" : ""}`}
                role="button"
                tabIndex={0}
                onClick={() => selectTask(task.id)}
                title="Select this task"
              >
                {task.title}
              </span>
              <span className="item-meta">
                {task.completed_pomodoros}/{task.estimate_pomodoros}
              </span>
              {task.status !== "done" && (
                <button
                  className="btn-icon"
                  onClick={() => completeTask(task.id)}
                  title="Mark done"
                >
                  ✓
                </button>
              )}
              <button className="btn-icon" onClick={() => removeTask(task.id)} title="Remove">
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
      <TaskForm />
    </div>
  );
}
