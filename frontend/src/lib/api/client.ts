import type { components } from "./schema";

type Schemas = components["schemas"];
export type User = Schemas["UserOut"];
export type Task = Schemas["TaskOut"];
export type Readiness = Schemas["ReadyResponse"];
type ErrorEnvelope = Schemas["ErrorResponse"];

const API_BASE = "/api";
const CSRF_HEADER = "X-Requested-With";
const CSRF_VALUE = "workmate";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }

  get isUnauthenticated(): boolean {
    return this.status === 401;
  }
}

function isErrorEnvelope(value: unknown): value is ErrorEnvelope {
  if (typeof value !== "object" || value === null || !("error" in value)) return false;
  const error = (value as { error: unknown }).error;
  return (
    typeof error === "object" &&
    error !== null &&
    typeof (error as { code?: unknown }).code === "string" &&
    typeof (error as { message?: unknown }).message === "string"
  );
}

async function readJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return undefined;
  try {
    return JSON.parse(text);
  } catch {
    return undefined;
  }
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  /** Status codes whose JSON body is a valid result rather than an error. */
  acceptStatuses?: number[];
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, acceptStatuses = [] } = options;
  const headers: Record<string, string> = { Accept: "application/json", [CSRF_HEADER]: CSRF_VALUE };
  if (body !== undefined) headers["Content-Type"] = "application/json";

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: "same-origin",
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "network_error", "Could not reach the server. Check your connection.");
  }

  const data = await readJson(response);
  if (response.ok || acceptStatuses.includes(response.status)) return data as T;
  if (isErrorEnvelope(data)) {
    throw new ApiError(response.status, data.error.code, data.error.message, data.error.details);
  }
  throw new ApiError(response.status, "http_error", `Request failed (${response.status}).`);
}

export const api = {
  login: (email: string, password: string) =>
    request<User>("/auth/login", { method: "POST", body: { email, password } }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  me: () => request<User>("/auth/me"),
  tasks: (limit = 20) => request<Task[]>(`/tasks?limit=${limit}`),
  // 503 still carries per-service results, which the dashboard displays.
  readiness: () => request<Readiness>("/health/ready", { acceptStatuses: [503] }),
};
