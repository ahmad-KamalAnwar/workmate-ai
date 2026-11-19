import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, api, request } from "./client";

function mockFetch(status: number, body?: unknown) {
  const fn = vi.fn().mockResolvedValue(
    new Response(body === undefined ? null : JSON.stringify(body), { status }),
  );
  vi.stubGlobal("fetch", fn);
  return fn;
}

afterEach(() => vi.unstubAllGlobals());

describe("request", () => {
  it("sends the CSRF header, JSON body and same-origin credentials", async () => {
    const fetchMock = mockFetch(200, { id: "1", email: "a@b.c", display_name: null, timezone: "UTC" });

    await api.login("a@b.c", "pw");

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/auth/login");
    expect(init.method).toBe("POST");
    expect(init.credentials).toBe("same-origin");
    expect(init.headers).toMatchObject({
      "X-Requested-With": "workmate",
      "Content-Type": "application/json",
    });
    expect(JSON.parse(init.body as string)).toEqual({ email: "a@b.c", password: "pw" });
  });

  it("turns the error envelope into an ApiError", async () => {
    mockFetch(401, { error: { code: "invalid_credentials", message: "Invalid email or password" } });

    const error = await api.login("a@b.c", "bad").catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 401, code: "invalid_credentials", message: "Invalid email or password" });
    expect((error as ApiError).isUnauthenticated).toBe(true);
  });

  it("reports a generic error when the body is not an envelope", async () => {
    mockFetch(502, "<html>bad gateway</html>");
    await expect(request("/x")).rejects.toMatchObject({ status: 502, code: "http_error" });
  });

  it("reports network failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(api.me()).rejects.toMatchObject({ status: 0, code: "network_error" });
  });

  it("returns undefined for empty 204 responses", async () => {
    mockFetch(204);
    await expect(api.logout()).resolves.toBeUndefined();
  });

  it("treats a 503 readiness body as a result, not an error", async () => {
    const body = { status: "degraded", checks: { database: "ok", redis: "error" } };
    mockFetch(503, body);
    await expect(api.readiness()).resolves.toEqual(body);
  });
});
