import { requestJson } from "./httpClient";

export const ConnectivityMode = {
  MOCK: "MOCK",
  LIVE: "LIVE",
} as const;

export type ConnectivityMode = (typeof ConnectivityMode)[keyof typeof ConnectivityMode];

export interface ConnectivityStatus {
  mode: ConnectivityMode;
  isConnected: boolean;
  message: string;
}

interface HealthResponse {
  status?: string;
}

export function isMockApiEnabled(): boolean {
  return import.meta.env.VITE_USE_MOCK_API !== "false";
}

/** Verifica la conectividad del Walking Skeleton contra /health o el modo mock. */
export async function checkBackendConnectivity(): Promise<ConnectivityStatus> {
  if (isMockApiEnabled()) {
    return {
      mode: ConnectivityMode.MOCK,
      isConnected: true,
      message: "Modo simulado activo (contratos CT-01, CT-06 y CT-09)",
    };
  }

  try {
    await requestJson<HealthResponse>("/health");
    return {
      mode: ConnectivityMode.LIVE,
      isConnected: true,
      message: "Conectado al backend FastAPI (/health)",
    };
  } catch {
    return {
      mode: ConnectivityMode.LIVE,
      isConnected: false,
      message: "Sin conexión con el backend FastAPI (/health)",
    };
  }
}
