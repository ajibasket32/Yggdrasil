/* eslint-disable @typescript-eslint/no-explicit-any */
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import ErrorBoundary from "./components/ErrorBoundary";
import CombatPanel from "./components/CombatPanel";
import NarrativeBox from "./components/NarrativeBox";
import WorldPanel from "./components/WorldPanel";
import ShopOverlay from "./components/ShopOverlay";
import GameCanvas from "./components/GameCanvas";
import portraitAtlasUrl from "./assets/characters/RPG_assets.png";
import { gameApi, getPlayerId } from "./services/gameApi";
import type {
  CharacterDefinitions,
  CharacterSummary,
  CharacterSheet,
  CombatActionType,
  CombatState,
  CreateCharacterInput,
  Equipment,
  EncounterDefinition,
  Dungeon,
  Faction,
  Inventory,
  JournalEntry,
  Location,
  Narrative,
  Npc,
  Quest,
  DialogueTopic,
  Shop,
  ShopItem,
  InnRestResult,
} from "./types/gameplay";

const statLabels = {
  strength: "Strength",
  dexterity: "Dexterity",
  agility: "Agility",
  vitality: "Vitality",
  intelligence: "Intelligence",
  wisdom: "Wisdom",
  charisma: "Charisma",
} as const;

const formValue = (data: FormData, name: string): string => {
  const value = data.get(name);
  return typeof value === "string" ? value : "";
};

const combatStorageKey = (characterId: string) =>
  `yggdrasil-active-combat:${characterId}`;

const combatSeed = (): number => {
  if (typeof crypto.getRandomValues === "function") {
    const values = crypto.getRandomValues(new Uint32Array(1));
    return (values[0] ?? 0) & 0x7fffffff;
  }
  return Date.now() & 0x7fffffff;
};

const App = () => {
  const playerId = useMemo(getPlayerId, []);
  const [definitions, setDefinitions] = useState<CharacterDefinitions | null>(
    null,
  );
  const [existingCharacters, setExistingCharacters] = useState<
    CharacterSummary[]
  >([]);
  const [character, setCharacter] = useState<CharacterSheet | null>(null);
  const [inventory, setInventory] = useState<Inventory | null>(null);
  const [equipment, setEquipment] = useState<Equipment | null>(null);
  const [locations, setLocations] = useState<Location[]>([]);
  const [encounters, setEncounters] = useState<EncounterDefinition[]>([]);
  const [combat, setCombat] = useState<CombatState | null>(null);
  const [quests, setQuests] = useState<Quest[]>([]);
  const [npcs, setNpcs] = useState<Npc[]>([]);
  const [factions, setFactions] = useState<Faction[]>([]);
  const [dungeons, setDungeons] = useState<Dungeon[]>([]);
  const [journal, setJournal] = useState<JournalEntry[]>([]);
  const [interactionText, setInteractionText] = useState<string | null>(null);
  const [narrative, setNarrative] = useState<Narrative | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentShop, setCurrentShop] = useState<Shop | null>(null);
  const [lastPurchase, setLastPurchase] = useState<string | null>(null);

  type MenuView =
    | "NONE"
    | "CHARACTER"
    | "WORLD_PANEL"
    | "ENCOUNTERS"
    | "TRAVEL"
    | "ENDING";
  const [menuView, setMenuView] = useState<MenuView>("NONE");

  const inspectCharacter = useCallback(
    async (characterId: string) => {
      const [
        sheet,
        nextInventory,
        nextEquipment,
        nextLocations,
        nextEncounters,
        nextQuests,
        nextNpcs,
        nextFactions,
        nextDungeons,
        nextJournal,
      ] = await Promise.all([
        gameApi.character(playerId, characterId),
        gameApi.inventory(playerId, characterId),
        gameApi.equipment(playerId, characterId),
        gameApi.locations(playerId, characterId),
        gameApi.encounters(playerId, characterId),
        gameApi.quests(playerId, characterId),
        gameApi.npcs(playerId, characterId),
        gameApi.factions(playerId, characterId),
        gameApi.dungeons(playerId, characterId),
        gameApi.journal(playerId, characterId),
      ]);
      setCharacter(sheet);
      setInventory(nextInventory);
      setEquipment(nextEquipment);
      setLocations(nextLocations);
      setEncounters(nextEncounters);
      setQuests(nextQuests);
      setNpcs(nextNpcs);
      setFactions(nextFactions);
      setDungeons(nextDungeons);
      setJournal(nextJournal);
      const activeCombatId = window.localStorage.getItem(
        combatStorageKey(characterId),
      );
      if (activeCombatId !== null) {
        try {
          setCombat(await gameApi.combat(playerId, activeCombatId));
        } catch {
          window.localStorage.removeItem(combatStorageKey(characterId));
        }
      }
    },
    [playerId],
  );

  useEffect(() => {
    const load = async () => {
      try {
        const [nextDefinitions, characters] = await Promise.all([
          gameApi.definitions(),
          gameApi.characters(playerId),
        ]);
        setDefinitions(nextDefinitions);
        setExistingCharacters(characters);
      } catch (caught) {
        setError(
          caught instanceof Error ? caught.message : "Unable to load game data",
        );
      } finally {
        setBusy(false);
      }
    };
    void load();
  }, [inspectCharacter, playerId]);

  const createCharacter = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const input: CreateCharacterInput = {
      name: formValue(data, "name"),
      race_id: formValue(data, "race"),
      gender: formValue(data, "gender"),
      alignment: formValue(
        data,
        "alignment",
      ) as CreateCharacterInput["alignment"],
      starting_job_id: formValue(data, "job"),
    };
    setBusy(true);
    setError(null);
    try {
      const created = await gameApi.createCharacter(
        playerId,
        input,
        crypto.randomUUID(),
      );
      await inspectCharacter(created.id);
      setMenuView("NONE");
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Character creation failed",
      );
    } finally {
      setBusy(false);
    }
  };

  const travel = async (destination: Location, characterId: string) => {
    setBusy(true);
    setError(null);
    try {
      await gameApi.travel(
        playerId,
        characterId,
        destination.id,
        crypto.randomUUID(),
      );
      await inspectCharacter(characterId);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Travel failed");
    } finally {
      setBusy(false);
    }
  };

  const startCombat = async (encounter: EncounterDefinition) => {
    if (character === null) return;
    setBusy(true);
    setError(null);
    try {
      const started = await gameApi.startCombat(
        playerId,
        character.id,
        encounter.id,
        combatSeed(),
        crypto.randomUUID(),
      );
      window.localStorage.setItem(
        combatStorageKey(character.id),
        started.combat_id,
      );
      setCombat(started);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Combat failed");
    } finally {
      setBusy(false);
    }
  };

  const combatAction = async (
    action: CombatActionType,
    skillId?: string,
    inventoryItemId?: string,
  ) => {
    if (combat === null) return;
    setBusy(true);
    setError(null);
    try {
      setCombat(
        await gameApi.combatAction(
          playerId,
          combat.combat_id,
          action,
          crypto.randomUUID(),
          skillId,
          inventoryItemId,
        ),
      );
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Combat action failed",
      );
    } finally {
      setBusy(false);
    }
  };

  const fleeCombat = async () => {
    if (combat === null) return;
    setBusy(true);
    setError(null);
    try {
      setCombat(
        await gameApi.fleeCombat(
          playerId,
          combat.combat_id,
          crypto.randomUUID(),
        ),
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Escape failed");
    } finally {
      setBusy(false);
    }
  };

  const leaveCombat = async () => {
    if (character === null) return;
    window.localStorage.removeItem(combatStorageKey(character.id));
    setCombat(null);
    setBusy(true);
    try {
      await inspectCharacter(character.id);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to refresh character",
      );
    } finally {
      setBusy(false);
    }
  };

  const questAction = async (
    quest: Quest,
    action: "accept" | "submit" | "fail" | "archive",
  ) => {
    if (character === null) return;
    setBusy(true);
    setError(null);
    try {
      await gameApi.questMutation(
        playerId,
        character.id,
        quest.id,
        action,
        crypto.randomUUID(),
      );
      await inspectCharacter(character.id);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Quest action failed",
      );
    } finally {
      setBusy(false);
    }
  };

  const npcAction = async (npc: Npc, action: "GREET" | "OFFER_HELP") => {
    if (character === null) return;
    setBusy(true);
    setError(null);
    try {
      const result = await gameApi.interact(
        playerId,
        character.id,
        npc.id,
        action,
        crypto.randomUUID(),
      );
      setInteractionText(result.result_text);
      await inspectCharacter(character.id);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "NPC interaction failed",
      );
    } finally {
      setBusy(false);
    }
  };

  const joinFaction = async (faction: Faction) => {
    if (character === null) return;
    setBusy(true);
    setError(null);
    try {
      await gameApi.joinFaction(
        playerId,
        character.id,
        faction.id,
        crypto.randomUUID(),
      );
      await inspectCharacter(character.id);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Faction join failed",
      );
    } finally {
      setBusy(false);
    }
  };

  const dialogue = async (npc: Npc, topic: DialogueTopic) => {
    if (character === null) return;
    setBusy(true);
    setError(null);
    try {
      setNarrative(
        await gameApi.dialogue(
          playerId,
          character.id,
          npc.id,
          topic,
          crypto.randomUUID(),
        ),
      );
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Dialogue unavailable",
      );
    } finally {
      setBusy(false);
    }
  };

  const questFraming = async (quest: Quest) => {
    if (character === null) return;
    setBusy(true);
    setError(null);
    try {
      setNarrative(
        await gameApi.questFraming(
          playerId,
          character.id,
          quest.id,
          crypto.randomUUID(),
        ),
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Story unavailable");
    } finally {
      setBusy(false);
    }
  };

  const describeLocation = async () => {
    if (character === null) return;
    setBusy(true);
    setError(null);
    try {
      setNarrative(
        await gameApi.locationDescription(
          playerId,
          character.id,
          character.current_location.id,
          crypto.randomUUID(),
        ),
      );
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Description unavailable",
      );
    } finally {
      setBusy(false);
    }
  };

  const dungeonAction = async (dungeon: Dungeon, action: "enter" | "clear") => {
    if (character === null) return;
    setBusy(true);
    setError(null);
    try {
      await gameApi.dungeonMutation(
        playerId,
        character.id,
        dungeon.id,
        action,
        crypto.randomUUID(),
      );
      await inspectCharacter(character.id);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Dungeon action failed",
      );
    } finally {
      setBusy(false);
    }
  };

  const openShop = useCallback(
    async (shopId: string) => {
      setBusy(true);
      setError(null);
      try {
        const shopData: Shop = await gameApi.shop(playerId, shopId);
        setCurrentShop(shopData);
      } catch (caught: any) {
        setError(
          caught instanceof Error ? caught.message : "Unable to open shop",
        );
      } finally {
        setBusy(false);
      }
    },
    [playerId],
  );

  const purchaseItem = useCallback(
    async (item: ShopItem) => {
      if (character === null || currentShop === null) return;
      setBusy(true);
      setError(null);
      setLastPurchase(null);
      try {
        await gameApi.purchase(
          playerId,
          character.id,
          currentShop.id,
          item.item_id,
          crypto.randomUUID(),
        );
        setLastPurchase(item.name);
        await inspectCharacter(character.id);
        setTimeout(() => setLastPurchase(null), 3000);
      } catch (caught: any) {
        setError(caught instanceof Error ? caught.message : "Purchase failed");
      } finally {
        setBusy(false);
      }
    },
    [character, currentShop, inspectCharacter, playerId],
  );

  const innRest = useCallback(
    async (npcId: string) => {
      if (character === null) return;
      setBusy(true);
      setError(null);
      try {
        const restResult: InnRestResult = await gameApi.rest(
          playerId,
          character.id,
          npcId,
          crypto.randomUUID(),
        );
        setInteractionText(
          `Rested at the Inn. Restored ${restResult.hp_restored} HP and ${restResult.mp_restored} MP.`,
        );
        await inspectCharacter(character.id);
      } catch (caught: any) {
        setError(caught instanceof Error ? caught.message : "Inn rest failed");
      } finally {
        setBusy(false);
      }
    },
    [character, inspectCharacter, playerId],
  );

  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  const saveGame = async () => {
    if (character === null) return;
    setBusy(true);
    setError(null);
    setSaveSuccess(false);
    try {
      await gameApi.createSave(playerId, character.id, crypto.randomUUID());
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Save failed");
    } finally {
      setBusy(false);
    }
  };

  const deleteCharacter = async () => {
    if (character === null) return;
    setBusy(true);
    try {
      await gameApi.deleteSave(playerId, character.id, crypto.randomUUID());
      setCharacter(null);
      setMenuView("NONE");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Deletion failed");
    } finally {
      setBusy(false);
    }
  };

  const triggerEnding = () => {
    if (
      confirm(
        "Are you sure you want to conclude your journey? This will end the MVP.",
      )
    ) {
      setMenuView("ENDING");
    }
  };

  if (busy && definitions === null) {
    return <main className="centered">Loading the character archive...</main>;
  }

  return (
    <main className={character !== null ? "jrpg-layout" : ""}>
      <ErrorBoundary>
        {character === null && definitions !== null && menuView === "NONE" && (
          <div className="title-screen">
            <div className="title-logo">Yggdrasil Chronicles</div>
            <p
              className="eyebrow"
              style={{ color: "#fff", marginBottom: "2rem" }}
            >
              v1.1 JRPG Polish Release
            </p>
            <div className="title-menu">
              {existingCharacters.length > 0 ? (
                <button
                  className="kenney-button"
                  onClick={() =>
                    existingCharacters[0] &&
                    void inspectCharacter(existingCharacters[0]?.id)
                  }
                >
                  Continue: {existingCharacters[0]?.name}
                </button>
              ) : (
                <div className="muted" style={{ marginBottom: "1rem" }}>
                  No existing chronicles found.
                </div>
              )}
              <button
                className="kenney-button"
                onClick={() => setMenuView("CHARACTER")}
              >
                New Game
              </button>
              <div
                className="muted"
                style={{ marginTop: "2rem", fontSize: "0.8rem" }}
              >
                Controls: WASD/Arrows to move, E to interact
              </div>
            </div>
          </div>
        )}

        {error !== null && (
          <p className="error" role="alert">
            {error}
          </p>
        )}

        {combat !== null && character !== null && (
          <>
            <GameCanvas
              mode="COMBAT"
              combatState={combat}
              locationName={character.current_location.name}
            />
            <div className="jrpg-ui-layer">
              <div className="bottom-panel">
                <CombatPanel
                  combat={combat}
                  skills={character.skills}
                  inventory={inventory}
                  busy={busy}
                  onAction={(action, skillId, inventoryItemId) => {
                    void combatAction(action, skillId, inventoryItemId);
                  }}
                  onFlee={() => void fleeCombat()}
                  onReturn={() => void leaveCombat()}
                />
              </div>
            </div>
          </>
        )}

        {character === null &&
        definitions !== null &&
        menuView === "CHARACTER" ? (
          <section className="creation-layout jrpg-panel">
            <div className="intro-panel" style={{ background: "transparent" }}>
              <p className="eyebrow">New Game</p>
              <h2>Create your character</h2>
              <div className="portrait-preview">
                <img src={portraitAtlasUrl} alt="Portrait" />
              </div>
              <p>
                Race, job, statistics, starting skills, inventory, and location
                are resolved by the game engine and persisted together.
              </p>
            </div>
            <form
              className="creation-form kenney-panel"
              onSubmit={(event) => {
                void createCharacter(event);
              }}
            >
              <label>
                Character name
                <input
                  name="name"
                  minLength={2}
                  maxLength={32}
                  pattern="[A-Za-z][A-Za-z '\-]*"
                  required
                  placeholder="Aster Vale"
                />
              </label>
              <label>
                Race
                <select name="race" required>
                  {definitions.races.map((race) => (
                    <option key={race.id} value={race.id}>
                      {race.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Starting job
                <select name="job" required>
                  {definitions.starting_jobs.map((job) => (
                    <option key={job.id} value={job.id}>
                      {job.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Gender
                <input name="gender" defaultValue="Unspecified" required />
              </label>
              <label>
                Alignment
                <select name="alignment" defaultValue="NEUTRAL">
                  <option value="GOOD">Good</option>
                  <option value="NEUTRAL">Neutral</option>
                  <option value="EVIL">Evil</option>
                </select>
              </label>
              <div style={{ display: "flex", gap: "1rem" }}>
                <button
                  type="button"
                  className="kenney-button secondary"
                  onClick={() => setMenuView("NONE")}
                >
                  Back
                </button>
                <button className="kenney-button" type="submit" disabled={busy}>
                  Create character
                </button>
              </div>
            </form>
          </section>
        ) : character !== null && combat === null ? (
          <>
            <GameCanvas
              mode="EXPLORATION"
              locationName={character.current_location.name}
              npcs={npcs}
              reachableLocations={locations.filter((l) => l.reachable)}
              encounters={encounters}
              onTravel={(loc) => void travel(loc, character.id)}
              onInteract={(npc) => void dialogue(npc, "GREETING")}
              onEncounter={(enc) => void startCombat(enc)}
            />
            <div className="jrpg-ui-layer">
              <div className="hud-overlay jrpg-panel">
                <div className="character-status-compact">
                  <div className="portrait-mini">
                    <img src={portraitAtlasUrl} alt="Portrait" />
                  </div>
                  <div style={{ flexGrow: 1 }}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        marginBottom: "0.5rem",
                      }}
                    >
                      <strong style={{ fontSize: "1.2rem", color: "#fef08a" }}>
                        {character.name}
                      </strong>
                      <span className="muted">
                        Lv {character.level} {character.current_job.name}
                      </span>
                    </div>

                    <div className="resource-bar-container">
                      <span className="resource-bar-label">HP</span>
                      <div className="resource-bar">
                        <div
                          className="resource-fill hp"
                          style={{
                            width: `${(character.current_hp / character.derived_stats.max_hp) * 100}%`,
                          }}
                        ></div>
                        <span className="resource-text">
                          {character.current_hp}/
                          {character.derived_stats.max_hp}
                        </span>
                      </div>
                    </div>

                    <div className="resource-bar-container">
                      <span className="resource-bar-label">MP</span>
                      <div className="resource-bar">
                        <div
                          className="resource-fill mp"
                          style={{
                            width: `${(character.current_mp / character.derived_stats.max_mp) * 100}%`,
                          }}
                        ></div>
                        <span className="resource-text">
                          {character.current_mp}/
                          {character.derived_stats.max_mp}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div
                  style={{
                    marginTop: "1rem",
                    borderTop: "1px solid #4a6fa5",
                    paddingTop: "0.5rem",
                    fontSize: "0.9rem",
                    color: "#89b4fa",
                  }}
                >
                  📍 {character.current_location.name}
                </div>
              </div>

              {(interactionText !== null || narrative !== null) && (
                <div className="narrative-container">
                  <div className="jrpg-panel" style={{ flexGrow: 1 }}>
                    {interactionText && (
                      <div className="narrative-text typing-effect">
                        {interactionText}
                      </div>
                    )}
                    {narrative && (
                      <NarrativeBox
                        narrative={narrative}
                        onClose={() => setNarrative(null)}
                      />
                    )}
                    {interactionText && !narrative && (
                      <div style={{ textAlign: "right", marginTop: "1rem" }}>
                        <button onClick={() => setInteractionText(null)}>
                          Close ▼
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div
                className="action-bar jrpg-panel"
                style={{ padding: "1rem" }}
              >
                <button onClick={() => setMenuView("TRAVEL")}>Travel</button>
                <button onClick={() => setMenuView("ENCOUNTERS")}>
                  Encounters
                </button>
                <button onClick={() => setMenuView("WORLD_PANEL")}>
                  Quests
                </button>
                <button onClick={() => setMenuView("CHARACTER")}>Status</button>
                <button onClick={() => void saveGame()}>
                  {saveSuccess ? "✓ Saved" : "Save Chronicle"}
                </button>
                <button onClick={triggerEnding} style={{ color: "#f87171" }}>
                  Conclude
                </button>
              </div>

              {menuView !== "NONE" && (
                <div
                  className="menu-modal-backdrop"
                  onClick={() => menuView !== "ENDING" && setMenuView("NONE")}
                >
                  <div
                    className="menu-modal-content"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {menuView !== "ENDING" && (
                      <button
                        className="menu-close-btn"
                        onClick={() => setMenuView("NONE")}
                      >
                        ×
                      </button>
                    )}

                    {menuView === "CHARACTER" && (
                      <div className="archive">
                        <section className="panel">
                          <h3>Attributes</h3>
                          <div className="stat-grid">
                            {Object.entries(statLabels).map(([key, label]) => (
                              <div key={key}>
                                <span>{label}</span>
                                <strong>
                                  {
                                    character.stats[
                                      key as keyof typeof character.stats
                                    ]
                                  }
                                </strong>
                              </div>
                            ))}
                          </div>
                        </section>
                        <section className="panel split-panel">
                          <div>
                            <h3>Job progress</h3>
                            {character.jobs.map((job) => (
                              <p key={job.job.id}>
                                <strong>{job.job.name}</strong> · Job level{" "}
                                {job.job_level}
                                {job.active ? " · Active" : ""}
                              </p>
                            ))}
                          </div>
                          <div>
                            <h3>Skills</h3>
                            {character.skills.map((skill) => (
                              <p key={skill.id}>
                                <strong>{skill.name}</strong> · Rank{" "}
                                {skill.skill_level}
                              </p>
                            ))}
                          </div>
                        </section>
                        <section className="panel split-panel">
                          <div>
                            <h3>Inventory</h3>
                            <p className="muted">
                              {inventory?.used_slots ?? 0}/
                              {inventory?.slot_count ?? 0} slots ·{" "}
                              {inventory?.total_weight ?? 0}/
                              {inventory?.max_weight ?? 0} weight
                            </p>
                            <ul>
                              {inventory?.items.map((item) => (
                                <li key={item.inventory_item_id}>
                                  <strong>{item.name}</strong> × {item.quantity}
                                  {item.is_quest_item ? " · Protected" : ""}
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <h3>Equipment</h3>
                            <ul>
                              {equipment?.slots.map((slot) => (
                                <li key={slot.slot_id}>
                                  <span>{slot.name}</span> ·{" "}
                                  {slot.item?.name ?? "Empty"}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </section>
                      </div>
                    )}

                    {menuView === "WORLD_PANEL" && (
                      <WorldPanel
                        quests={quests}
                        npcs={npcs}
                        factions={factions}
                        dungeons={dungeons}
                        journal={journal}
                        busy={busy}
                        interactionText={interactionText}
                        narrative={narrative}
                        onQuestAction={(quest, action) =>
                          void questAction(quest, action)
                        }
                        onNpcAction={(npc, action) =>
                          void npcAction(npc, action)
                        }
                        onDialogue={(npc, topic) => {
                          void dialogue(npc, topic);
                          setMenuView("NONE");
                        }}
                        onQuestFraming={(quest) => {
                          void questFraming(quest);
                          setMenuView("NONE");
                        }}
                        onCloseNarrative={() => setNarrative(null)}
                        onJoinFaction={(faction) => void joinFaction(faction)}
                        onDungeonAction={(dungeon, action) =>
                          void dungeonAction(dungeon, action)
                        }
                        characterGold={character.gold}
                        onShopOpen={(shopId) => {
                          void openShop(shopId);
                          setMenuView("NONE");
                        }}
                        onInnRest={(npcId) => {
                          void innRest(npcId);
                          setMenuView("NONE");
                        }}
                      />
                    )}

                    {menuView === "ENCOUNTERS" && (
                      <section className="panel">
                        <h3>Encounters</h3>
                        {encounters.length === 0 ? (
                          <p className="muted">
                            No combat encounters at this location.
                          </p>
                        ) : (
                          <div className="encounter-grid">
                            {encounters.map((encounter) => (
                              <article key={encounter.id}>
                                <p className="eyebrow">
                                  {encounter.difficulty}
                                </p>
                                <h4>{encounter.name}</h4>
                                <p>
                                  Level {encounter.monster_level}{" "}
                                  {encounter.monster_name}
                                </p>
                                <p className="muted">
                                  {encounter.reward_experience} XP /{" "}
                                  {encounter.reward_gold} gold
                                </p>
                                <button
                                  type="button"
                                  disabled={busy}
                                  onClick={() => {
                                    void startCombat(encounter);
                                    setMenuView("NONE");
                                  }}
                                >
                                  Begin combat
                                </button>
                              </article>
                            ))}
                          </div>
                        )}
                      </section>
                    )}

                    {menuView === "TRAVEL" && (
                      <section className="panel">
                        <div className="section-heading">
                          <h3>Known world</h3>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => {
                              void describeLocation();
                              setMenuView("NONE");
                            }}
                          >
                            Observe surroundings
                          </button>
                        </div>
                        <div className="location-grid">
                          {locations
                            .filter(
                              (location) =>
                                location.discovered || location.reachable,
                            )
                            .map((location) => (
                              <article key={location.id}>
                                <p className="eyebrow">
                                  Danger {location.danger_level}
                                </p>
                                <h4>{location.name}</h4>
                                <p>{location.description}</p>
                                {location.reachable &&
                                  location.id !==
                                    character.current_location.id && (
                                    <button
                                      type="button"
                                      disabled={busy}
                                      onClick={() => {
                                        void travel(location, character.id);
                                        setMenuView("NONE");
                                      }}
                                    >
                                      Travel here
                                    </button>
                                  )}
                                {location.id ===
                                  character.current_location.id && (
                                  <span className="current">
                                    Current location
                                  </span>
                                )}
                              </article>
                            ))}
                        </div>
                      </section>
                    )}

                    {menuView === "ENDING" && (
                      <div style={{ textAlign: "center", padding: "2rem" }}>
                        <h2 style={{ fontSize: "3rem", marginBottom: "2rem" }}>
                          The End
                        </h2>
                        <p style={{ fontSize: "1.2rem", marginBottom: "2rem" }}>
                          Thank you for playing the Yggdrasil Chronicles MVP
                          Candidate. Your journey as {character.name} the{" "}
                          {character.current_job.name} ends here.
                        </p>
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "center",
                            gap: "1rem",
                          }}
                        >
                          <button onClick={() => setMenuView("NONE")}>
                            Return to Game
                          </button>
                          <button
                            onClick={() => void deleteCharacter()}
                            style={{ borderColor: "#f87171", color: "#f87171" }}
                          >
                            Finalize & Delete Save
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
            {currentShop && (
              <ShopOverlay
                shop={currentShop}
                characterGold={character.gold}
                busy={busy}
                onPurchase={(item) => void purchaseItem(item)}
                onClose={() => {
                  setCurrentShop(null);
                  setError(null);
                  setLastPurchase(null);
                }}
                lastPurchase={lastPurchase}
                error={error}
              />
            )}
          </>
        ) : null}
      </ErrorBoundary>
    </main>
  );
};

export default App;
