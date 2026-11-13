import type { HealthCheckState } from "../hooks/useBackendHealth";

interface HealthCheckPanelProps {
  health: HealthCheckState;
}

export function HealthCheckPanel({ health }: HealthCheckPanelProps) {
  if (health.kind === "loading") {
    return <p>Consultando el backend…</p>;
  }
  if (health.kind === "error") {
    return <p>Backend: ERROR — no se pudo contactar el backend.</p>;
  }
  return (
    <ul>
      <li>Backend: {health.data.status === "ok" ? "OK" : "ERROR"}</li>
      <li>Base de datos: {health.data.database === "ok" ? "OK" : "ERROR"}</li>
    </ul>
  );
}
