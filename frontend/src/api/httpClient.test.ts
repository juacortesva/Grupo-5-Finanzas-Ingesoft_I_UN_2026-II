import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, requestJson, setAuthTokenProvider } from "./httpClient";

describe("httpClient", () => {
  afterEach(() => {
    setAuthTokenProvider(() => null);
    vi.restoreAllMocks();
  });

  it("test_request_json_when_token_configured_then_sends_bearer_header", async () => {
    // Arrange
    setAuthTokenProvider(() => "jwt-demo-token");
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, { status: 204 }),
    );

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
});
