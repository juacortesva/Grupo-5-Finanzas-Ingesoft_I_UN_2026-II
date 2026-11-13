import { afterEach, describe, expect, it, vi } from "vitest";
import { checkBackendConnectivity, ConnectivityMode, isMockApiEnabled } from "./healthService";

describe("healthService", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("test_is_mock_api_enabled_when_env_not_false_then_returns_true", () => {
    // Arrange
    vi.stubEnv("VITE_USE_MOCK_API", "true");

    // Act
    const result = isMockApiEnabled();

    // Assert
    expect(result).toBe(true);
  });

  it("test_check_connectivity_when_mock_enabled_then_returns_mock_mode", async () => {
    // Arrange
    vi.stubEnv("VITE_USE_MOCK_API", "true");

    // Act
    const status = await checkBackendConnectivity();

    // Assert
    expect(status.mode).toBe(ConnectivityMode.MOCK);
    expect(status.isConnected).toBe(true);
    expect(status.message).toContain("Modo simulado activo");
  });

  it("test_check_connectivity_when_live_and_backend_healthy_then_returns_connected", async () => {
    // Arrange
    vi.stubEnv("VITE_USE_MOCK_API", "false");
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ status: "healthy" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    // Act
    const status = await checkBackendConnectivity();

    // Assert
    expect(status.mode).toBe(ConnectivityMode.LIVE);
    expect(status.isConnected).toBe(true);
    expect(status.message).toBe("Conectado al backend FastAPI (/api/health)");
    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const requestedUrl = fetchSpy.mock.calls[0]?.[0] as string;
    expect(requestedUrl).toContain("/api/health");
  });

  it("test_check_connectivity_when_live_and_backend_fails_then_returns_disconnected", async () => {
    // Arrange
    vi.stubEnv("VITE_USE_MOCK_API", "false");
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network Error"));

    // Act
    const status = await checkBackendConnectivity();

    // Assert
    expect(status.mode).toBe(ConnectivityMode.LIVE);
    expect(status.isConnected).toBe(false);
    expect(status.message).toBe("Sin conexión con el backend FastAPI (/api/health)");
  });
});
