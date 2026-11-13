// Cliente del endpoint técnico GET /api/health (verificación de infraestructura).

export interface HealthResponse {
  status: string;
  database: string;
}

function isHealthResponse(value: unknown): value is HealthResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return typeof candidate.status === "string" && typeof candidate.database === "string";
}

export async function fetchHealth(): Promise<HealthResponse> {
  // 503 también trae cuerpo JSON válido (base de datos inaccesible), así que no
  // se descarta la respuesta por su código HTTP.
  const response = await fetch("/api/health");
  const body: unknown = await response.json();
  if (!isHealthResponse(body)) {
    throw new Error("Respuesta de /api/health con formato inesperado.");
  }
  return body;
}
