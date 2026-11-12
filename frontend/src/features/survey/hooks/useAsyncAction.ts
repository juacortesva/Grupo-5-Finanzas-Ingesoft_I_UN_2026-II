import { useCallback, useState } from "react";

import type { AsyncActionState } from "../types";

/** Ejecuta una llamada asíncrona y expone datos, error y estado de carga. */
export function useAsyncAction<T>(action: () => Promise<T>): AsyncActionState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      setData(await action());
    } catch (err: unknown) {
      setData(null);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [action]);

  return { data, error, loading, run };
}
