import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/client";

import { LoginForm } from "./login-form";

async function fillAndSubmit(password = "secret password") {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Email"), "me@example.com");
  await user.type(screen.getByLabelText("Password"), password);
  await user.click(screen.getByRole("button", { name: "Sign in" }));
  return user;
}

describe("LoginForm", () => {
  it("submits the entered credentials", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<LoginForm onSubmit={onSubmit} />);

    await fillAndSubmit();

    expect(onSubmit).toHaveBeenCalledWith("me@example.com", "secret password");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows the API error, clears the password and focuses it", async () => {
    const onSubmit = vi
      .fn()
      .mockRejectedValue(new ApiError(401, "invalid_credentials", "Invalid email or password"));
    render(<LoginForm onSubmit={onSubmit} />);

    await fillAndSubmit();

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password");
    const password = screen.getByLabelText("Password");
    expect(password).toHaveValue("");
    expect(password).toHaveFocus();
  });

  it("disables the button while signing in", async () => {
    let resolve!: () => void;
    const onSubmit = vi.fn(() => new Promise<void>((r) => (resolve = r)));
    render(<LoginForm onSubmit={onSubmit} />);

    await fillAndSubmit();

    const button = screen.getByRole("button", { name: "Signing in…" });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
    resolve();
    expect(await screen.findByRole("button", { name: "Sign in" })).toBeEnabled();
  });

  it("does not submit with empty fields", async () => {
    const onSubmit = vi.fn();
    render(<LoginForm onSubmit={onSubmit} />);
    await userEvent.setup().click(screen.getByRole("button", { name: "Sign in" }));
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
