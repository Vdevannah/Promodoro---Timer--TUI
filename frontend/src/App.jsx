import "./App.css";
import { useTimerSocket } from "./hooks/useTimerSocket";
import TimerCard from "./components/TimerCard";
import TaskList from "./components/TaskList";
import TemplateList from "./components/TemplateList";
import SettingsPanel from "./components/SettingsPanel";
import ReportPanel from "./components/ReportPanel";

export default function App() {
  const { state, connected } = useTimerSocket();

  return (
    <div className="app">
      <header className="app-header">
        <h1>Pomodoro Timer</h1>
        <span className={`connection${connected ? " online" : ""}`}>
          <span className="connection-dot" />
          {connected ? "Connected" : "Connecting..."}
        </span>
      </header>

      {!state ? (
        <p className="empty-note">Waiting for the server...</p>
      ) : (
        <>
          <TimerCard timer={state.timer} />
          <div className="grid-2">
            <TaskList tasks={state.tasks} selectedTaskId={state.selected_task_id} />
            <TemplateList templates={state.templates} />
          </div>
          <SettingsPanel settings={state.settings} />
          <ReportPanel />
        </>
      )}
    </div>
  );
}
