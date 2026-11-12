/** Estado expuesto por los hooks que llaman a la API del Walking Skeleton. */
export interface AsyncActionState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  run: () => Promise<void>;
}
