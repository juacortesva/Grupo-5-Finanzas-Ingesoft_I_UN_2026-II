import { getHealth, type HealthResponse } from "../../api/client";
import { type AsyncActionState, useAsyncAction } from "./useAsyncAction";

export function useHealth(): AsyncActionState<HealthResponse> {
  return useAsyncAction(getHealth);
}
