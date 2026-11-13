/** Cliente HTTP base preparado para el backend FastAPI y manejo estándar de errores. */

const DEFAULT_ERROR_MESSAGE = "Ocurrió un error inesperado al comunicarse con el servidor.";

const HTTP_ERROR_MESSAGES: Readonly<Record<number, string>> = {
  401: "Tu sesión no es válida o ha expirado. Inicia sesión nuevamente.",
  404: "No se encontró la encuesta solicitada.",
  409: "La encuesta ya fue completada y no admite modificaciones.",
  422: "Los datos enviados no son válidos. Revisa tu selección.",
  503: "No fue posible completar la evaluación en este momento. Intenta más tarde.",
};

export interface HttpRequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  headers?: Record<string, string>;
}

/** Error tipado de la API con código HTTP y detalle sanitizado. */
export class ApiError extends Error {
  public readonly status: number;
  public readonly detail: string;

  constructor(status: number, detail: string) {
    super(HTTP_ERROR_MESSAGES[status] ?? DEFAULT_ERROR_MESSAGE);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

type TokenProvider = () => string | null;

let tokenProvider: TokenProvider = () => null;

/** Configura el proveedor de token Bearer inyectado desde el módulo de autenticación. */
export function setAuthTokenProvider(provider: TokenProvider): void {
  tokenProvider = provider;
}

/**
 * Resuelve el token Bearer para la petición según CT-02 y ADR-0006:
 * 1. Proveedor configurado vía setAuthTokenProvider (si retorna valor no vacío).
 * 2. Variable de entorno VITE_DEV_AUTH_TOKEN.
 * 3. Token almacenado en localStorage ("auth_token").
 * 4. Fallback provisional de Fase 0 a "dev-user-1" mientras la autenticación
 *    provisional esté activa (desactivable con VITE_ENABLE_DEV_AUTH="false").
 */
export function resolveAuthToken(): string | null {
  const customToken = tokenProvider();
  if (customToken !== null && customToken.trim().length > 0) {
    return customToken;
  }

  const envToken = import.meta.env.VITE_DEV_AUTH_TOKEN;
  if (typeof envToken === "string" && envToken.trim().length > 0) {
    return envToken;
  }

  try {
    const storageToken = globalThis.localStorage?.getItem("auth_token");
    if (typeof storageToken === "string" && storageToken.trim().length > 0) {
      return storageToken;
    }
  } catch {
    // Entorno sin acceso a localStorage (por ejemplo, SSR o sandbox restringido).
  }

  if (import.meta.env.VITE_ENABLE_DEV_AUTH !== "false") {
    return "dev-user-1";
  }

  return null;
}

function hasDetailField(payload: unknown): payload is { detail: string } {
  if (typeof payload !== "object" || payload === null) {
    return false;
  }
  const candidate = payload as Record<string, unknown>;
  return typeof candidate.detail === "string" && candidate.detail.length > 0;
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const data: unknown = await response.json();
    if (hasDetailField(data)) {
      return data.detail;
    }
  } catch {
    // Respuesta sin cuerpo JSON válido.
  }
  return HTTP_ERROR_MESSAGES[response.status] ?? DEFAULT_ERROR_MESSAGE;
}

function resolveBaseUrl(): string {
  const configuredUrl = import.meta.env.VITE_API_URL;
  if (typeof configuredUrl === "string" && configuredUrl.trim().length > 0) {
    return configuredUrl.replace(/\/+$/, "");
  }
  return "";
}

/** Ejecuta una petición HTTP JSON aplicando autenticación Bearer y parseo de errores. */
export async function requestJson<T>(path: string, options: HttpRequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...options.headers,
  };

  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const token = resolveAuthToken();
  if (token !== null && token.trim().length > 0) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${resolveBaseUrl()}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const detail = await parseErrorDetail(response);
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const data: unknown = await response.json();
  return data as T;
}
