import { useEffect, useRef, useState } from "react";

const WS_URL = "ws://127.0.0.1:8000/api/ws";

export function useTimerSocket() {
  const [state, setState] = useState(null);
  const [connected, setConnected] = useState(false);
  const [lastPhaseChange, setLastPhaseChange] = useState(null);
  const retryRef = useRef(0);

  useEffect(() => {
    let socket;
    let closedByEffect = false;
    let retryTimeout;

    function connect() {
      socket = new WebSocket(WS_URL);

      socket.onopen = () => {
        retryRef.current = 0;
        setConnected(true);
      };

      socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        setState(message.state);
        if (message.type === "phase_change") {
          setLastPhaseChange({ finishedPhase: message.finished_phase, at: Date.now() });
        }
      };

      socket.onclose = () => {
        setConnected(false);
        if (closedByEffect) return;
        const delay = Math.min(1000 * 2 ** retryRef.current, 10000);
        retryRef.current += 1;
        retryTimeout = setTimeout(connect, delay);
      };

      socket.onerror = () => {
        socket.close();
      };
    }

    connect();

    return () => {
      closedByEffect = true;
      clearTimeout(retryTimeout);
      socket?.close();
    };
  }, []);

  return { state, connected, lastPhaseChange };
}
