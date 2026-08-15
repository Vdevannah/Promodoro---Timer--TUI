import { pauseTimer, resetTimer, startTimer } from "../api/client";

function formatClock(totalSeconds) {
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

export default function TimerCard({ timer }) {
  return (
    <div className="card timer-card">
      <div className="timer-phase">{timer.phase}</div>
      <div className="timer-clock">{formatClock(timer.remaining)}</div>
      <p className="timer-task">
        {timer.selected_task_title
          ? `Working on: ${timer.selected_task_title}`
          : "No task selected"}
      </p>
      <div className="timer-controls">
        <button className="btn btn-primary" onClick={startTimer} disabled={timer.running}>
          Start
        </button>
        <button className="btn" onClick={pauseTimer} disabled={!timer.running}>
          Pause
        </button>
        <button className="btn" onClick={resetTimer}>
          Reset
        </button>
      </div>
    </div>
  );
}
