import { useEffect, useState } from "react";

import { fetchHealth, type HealthResponse } from "../../api/health";

export type HealthCheckState =
  { kind: "loading" } | { kind: "ok"; data: HealthResponse } | { kind: "error" };

export function useBackendHealth(): HealthCheckState {
  const [state, setState] = useState<HealthCheckState>({ kind: "loading" });

  useEffect(() => {
    let isActive = true;
    fetchHealth()
      .then((data) => {
        if (isActive) setState({ kind: "ok", data });
      })
      .catch(() => {
        if (isActive) setState({ kind: "error" });
      });
    return () => {
      isActive = false;
    };
  }, []);

  return state;
}
