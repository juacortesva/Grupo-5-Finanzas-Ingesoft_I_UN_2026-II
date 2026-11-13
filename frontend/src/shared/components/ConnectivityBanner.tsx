import { ConnectivityMode, ConnectivityStatus } from "../../api/healthService";

interface ConnectivityBannerProps {
  status: ConnectivityStatus;
}

export function ConnectivityBanner({ status }: ConnectivityBannerProps) {
  const toneClass =
    status.mode === ConnectivityMode.MOCK
      ? "banner--mock"
      : status.isConnected
        ? "banner--live"
        : "banner--offline";

  return (
    <div className={`connectivity-banner ${toneClass}`} role="status">
      <span className="connectivity-dot" aria-hidden="true" />
      <span>{status.message}</span>
    </div>
  );
}
