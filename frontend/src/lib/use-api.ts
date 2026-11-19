"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "@/lib/api/client";

export type AsyncState<T> =
  | { status: "loading" }
  | { status: "error"; error: ApiError }
  | { status: "success"; data: T };

function toApiError(error: unknown): ApiError {
  return error instanceof ApiError
    ? error
    : new ApiError(0, "unexpected_error", "Something went wrong. Please try again.");
}

/** Run `fn` on mount; `reload` re-runs it. Results from stale calls are ignored. */
export function useApi<T>(fn: () => Promise<T>): AsyncState<T> & { reload: () => void } {
  const [state, setState] = useState<AsyncState<T>>({ status: "loading" });
  const callId = useRef(0);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const reload = useCallback(() => {
    const id = ++callId.current;
    setState({ status: "loading" });
    fnRef.current().then(
      (data) => id === callId.current && setState({ status: "success", data }),
      (error: unknown) =>
        id === callId.current && setState({ status: "error", error: toApiError(error) }),
    );
  }, []);

  useEffect(() => {
    const ids = callId;
    reload();
    return () => {
      ids.current++; // ignore in-flight results after unmount
    };
  }, [reload]);

  return { ...state, reload };
}
