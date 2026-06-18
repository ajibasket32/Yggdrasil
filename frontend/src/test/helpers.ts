import { fireEvent, screen } from "@testing-library/react";

export const renderAppAtTitleScreen = async () => {
  expect(await screen.findByText("Yggdrasil Chronicles")).toBeInTheDocument();
};

export const startNewGame = async () => {
  const newGameBtn = await screen.findByRole("button", { name: "New Game" });
  fireEvent.click(newGameBtn);
  expect(
    await screen.findByRole("heading", { name: "Create your character" }),
  ).toBeInTheDocument();
};

export const continueExistingGame = async (characterName: string) => {
  const continueBtn = await screen.findByRole("button", {
    name: new RegExp(`Continue: ${characterName}`),
  });
  fireEvent.click(continueBtn);
  await screen.findByText(characterName);
};

export const createCharacterFromTitleFlow = async (name: string) => {
  await startNewGame();
  fireEvent.change(screen.getByLabelText("Character name"), {
    target: { value: name },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create character" }));
  await screen.findByText(name);
};

export const openMenu = (menuName: string) => {
  fireEvent.click(screen.getByRole("button", { name: menuName }));
};
