import { HealthCheckPanel } from "./shared/components/HealthCheckPanel";
import { useBackendHealth } from "./shared/hooks/useBackendHealth";

// Pantalla provisional de infraestructura: comprueba que el navegador llega al
// backend (vía nginx) y que el backend llega a PostgreSQL. El equipo la
// reemplaza con la primera pantalla real del Walking Skeleton.
export default function App() {
  const health = useBackendHealth();

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>Asesor Financiero Personal</h1>
      <p>Verificación de infraestructura (team-5)</p>
      <HealthCheckPanel health={health} />
    </main>
  );
}
