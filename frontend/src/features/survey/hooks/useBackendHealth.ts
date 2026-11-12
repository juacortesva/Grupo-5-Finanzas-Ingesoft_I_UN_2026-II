import { getHealth, type HealthResponse } from "../../../api/client";
import type { AsyncActionState } from "../types";
import { useAsyncAction } from "./useAsyncAction";

/** Consulta GET /api/v1/health (FastAPI + PostgreSQL). */
export function useBackendHealth(): AsyncActionState<HealthResponse> {
  return useAsyncAction(getHealth);
}
