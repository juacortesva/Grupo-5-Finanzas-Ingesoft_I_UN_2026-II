import { useEffect, useState } from "react";

// Pantalla provisional de infraestructura: solo comprueba que el navegador
// llega al backend (vía nginx) y que el backend llega a PostgreSQL.
// La reemplaza el equipo con la primera pantalla real del Walking Skeleton.

interface HealthResponse {
  status: string;
  database: string;
}

type CheckState =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthResponse }
  | { kind: "error"; message: string };

export default function App() {
  const [check, setCheck] = useState<CheckState>({ kind: "loading" });

  useEffect(() => {
    fetch("/api/health")
      .then(async (response) => {
        const data = (await response.json()) as HealthResponse;
        setCheck({ kind: "ok", data });
      })
      .catch(() => {
        setCheck({ kind: "error", message: "No se pudo contactar el backend." });
      });
  }, []);

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>Asesor Financiero Personal</h1>
      <p>Verificación de infraestructura (team-5)</p>
      {check.kind === "loading" && <p>Consultando el backend…</p>}
      {check.kind === "error" && <p>Backend: ERROR — {check.message}</p>}
      {check.kind === "ok" && (
        <ul>
          <li>Backend: {check.data.status === "ok" ? "OK" : "ERROR"}</li>
          <li>Base de datos: {check.data.database === "ok" ? "OK" : "ERROR"}</li>
        </ul>
      )}
    </main>
  );
}
