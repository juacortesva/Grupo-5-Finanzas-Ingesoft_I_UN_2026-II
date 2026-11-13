import { useEffect, useState } from "react";
import {
  ConnectivityMode,
  ConnectivityStatus,
  checkBackendConnectivity,
} from "./api/healthService";
import { SurveyView } from "./features/survey/pages/SurveyView";
import { ConnectivityBanner } from "./shared/components/ConnectivityBanner";

const INITIAL_CONNECTIVITY: ConnectivityStatus = {
  mode: ConnectivityMode.MOCK,
  isConnected: true,
  message: "Verificando conectividad con el servidor...",
};

export function App() {
  const [connectivity, setConnectivity] = useState<ConnectivityStatus>(INITIAL_CONNECTIVITY);

  useEffect(() => {
    let isMounted = true;
    void checkBackendConnectivity().then((status) => {
      if (isMounted) {
        setConnectivity(status);
      }
    });
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="app-kicker">Grupo 5 · Ingeniería de Software I</p>
          <h1 className="app-title">Asesor Financiero Personal</h1>
          <p className="app-subtitle">
            Responde esta encuesta breve (menos de 3 minutos) para descubrir tu perfil inicial.
          </p>
        </div>
        <ConnectivityBanner status={connectivity} />
      </header>

      <main className="app-main">
        <SurveyView />
      </main>
    </div>
  );
}

export default App;
