import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, requestJson, resolveAuthToken, setAuthTokenProvider } from "./httpClient";

describe("httpClient", () => {
  afterEach(() => {
    setAuthTokenProvider(() => null);
    globalThis.localStorage?.clear();
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("test_request_json_when_token_configured_then_sends_bearer_header", async () => {
    // Arrange
    setAuthTokenProvider(() => "jwt-demo-token");
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(null, { status: 204 }));

    // Act
    await requestJson<void>("/api/surveys/123/answers", {
      method: "PUT",
      body: { questionId: 1, selectedOption: 2 },
    });

    // Assert
    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const requestInit = fetchSpy.mock.calls[0]?.[1];
    const headers = requestInit?.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer jwt-demo-token");
  });

  it("test_request_json_when_api_returns_409_detail_then_throws_api_error", async () => {
    // Arrange
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Encuesta ya cerrada" }), {
        status: 409,
        headers: { "Content-Type": "application/json" },
      }),
    );

    // Act & Assert
    const pendingRequest = requestJson("/api/surveys/123/complete", { method: "POST" });
    await expect(pendingRequest).rejects.toMatchObject({
      name: "ApiError",
      status: 409,
      detail: "Encuesta ya cerrada",
    } satisfies Partial<ApiError>);
  });

  it("test_resolve_auth_token_when_no_token_in_prod_or_dev_then_returns_dev_user_1", () => {
    // Arrange
    vi.stubEnv("DEV", false);
    vi.stubEnv("VITE_DEV_AUTH_TOKEN", "");
    vi.stubEnv("VITE_ENABLE_DEV_AUTH", "true");

    // Act
    const token = resolveAuthToken();

    // Assert
    expect(token).toBe("dev-user-1");
  });

  it("test_resolve_auth_token_when_dev_auth_disabled_then_returns_null", () => {
    // Arrange
    vi.stubEnv("VITE_DEV_AUTH_TOKEN", "");
    vi.stubEnv("VITE_ENABLE_DEV_AUTH", "false");

    // Act
    const token = resolveAuthToken();

    // Assert
    expect(token).toBeNull();
  });

  it("test_resolve_auth_token_when_storage_has_token_then_returns_storage_token", () => {
    // Arrange
    globalThis.localStorage?.setItem("auth_token", "storage-session-token");

    // Act
    const token = resolveAuthToken();

    // Assert
    expect(token).toBe("storage-session-token");
  });

  it("test_resolve_auth_token_when_env_token_set_then_returns_env_token", () => {
    // Arrange
    vi.stubEnv("VITE_DEV_AUTH_TOKEN", "custom-env-token");

    // Act
    const token = resolveAuthToken();

    // Assert
    expect(token).toBe("custom-env-token");
  });
});
