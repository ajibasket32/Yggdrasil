import { fireEvent, render, screen } from "@testing-library/react";

import NarrativeBox from "./NarrativeBox";

it("presents bounded JRPG narrative without free-form input", () => {
  const onClose = vi.fn();
  render(
    <NarrativeBox
      narrative={{
        speaker_name: "Warden Elian",
        text: "The old road is quiet, but the roots are listening.",
        tone: "wary",
        tags: ["local-news"],
        fallback_used: true,
        cached: true,
        prompt_version: "npc-dialogue-v1",
        context_memory_count: 2,
        available_topics: ["GREETING", "QUEST", "LOCAL_NEWS", "FAREWELL"],
      }}
      onClose={onClose}
    />,
  );

  expect(screen.getByLabelText("Story dialogue")).toBeInTheDocument();
  expect(screen.getByText("Local narration")).toBeInTheDocument();
  expect(
    screen.getByText(/Grounded in 2 relevant memories/),
  ).toBeInTheDocument();
  expect(screen.queryByRole("textbox")).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  expect(onClose).toHaveBeenCalledOnce();
});
