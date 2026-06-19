import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ErrorBoundary from "./ErrorBoundary";

const ThrowingChild = () => {
  throw new Error("Map renderer failed");
};

describe("ErrorBoundary", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders children during normal operation", () => {
    render(
      <ErrorBoundary>
        <p>Exploration ready</p>
      </ErrorBoundary>,
    );

    expect(screen.getByText("Exploration ready")).toBeInTheDocument();
  });

  it("shows a recoverable fallback when a child crashes", () => {
    const preventExpectedError = (event: ErrorEvent) => {
      if (event.error?.message === "Map renderer failed") {
        event.preventDefault();
      }
    };
    window.addEventListener("error", preventExpectedError);
    vi.spyOn(console, "error").mockImplementation(() => undefined);

    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>,
    );

    expect(
      screen.getByRole("heading", { name: "Something went wrong." }),
    ).toBeInTheDocument();
    expect(screen.getByText("Map renderer failed")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Reload Page" }),
    ).toBeInTheDocument();
    window.removeEventListener("error", preventExpectedError);
  });
});
