import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import ErrorBoundary from "./components/ErrorBoundary";
import CombatPanel from "./components/CombatPanel";
import WorldPanel from "./components/WorldPanel";
import GameCanvas from "./components/GameCanvas";
import { gameApi, getPlayerId } from "./services/gameApi";
import type {
  CharacterDefinitions,
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
  /* v8 ignore next 4 */
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
        if (characters[0] !== undefined) {
          await inspectCharacter(characters[0].id);
        }
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
    /* v8 ignore next */
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

  const saveGame = async () => {
    if (character === null) return;
    setBusy(true);
    setError(null);
    try {
      await gameApi.createSave(playerId, character.id, crypto.randomUUID());
      alert("Chronicle persisted successfully.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Save failed");
    } finally {
      setBusy(false);
    }
  };

  const deleteCharacter = async () => {
    /* v8 ignore next */
    if (character === null) return;
    if (!confirm("Are you sure you want to end this chronicle?")) return;
    setBusy(true);
    try {
      await gameApi.deleteSave(playerId, character.id, crypto.randomUUID());
      setCharacter(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Deletion failed");
    } finally {
      setBusy(false);
    }
  };

  if (busy && definitions === null) {
    return <main className="centered">Loading the character archive...</main>;
  }

  return (
    <main>
      <ErrorBoundary>
        <header className="masthead">
        <div>
          <img
            src="assets/ui/rpg/iconCircle_beige.png"
            alt=""
            className="logo-icon"
          />
          <div>
            <p className="eyebrow">Yggdrasil Chronicles</p>
            <h1>Playable Vertical Slice</h1>
          </div>
        </div>
        <p className="release-mark">v0.10 Valeria Region</p>
      </header>

      {error !== null && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {combat !== null && character !== null ? (
        <>
          <GameCanvas mode="COMBAT" />
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
        </>
      ) : character === null && definitions !== null ? (
        <section className="creation-layout">
          <div className="intro-panel">
            <p className="eyebrow">Begin the chronicle</p>
            <h2>Create your character</h2>
            <div className="portrait-preview">
              <img src="assets/characters/RPG_assets.png" alt="Portrait" />
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
            <button type="submit" disabled={busy}>
              Create character
            </button>
          </form>
        </section>
      ) : character !== null ? (
        <div className="archive">
          <GameCanvas mode="EXPLORATION" />
          <div className="save-toolbar">
            <button
              type="button"
              disabled={busy}
              onClick={() => void saveGame()}
            >
              Save Game
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => void deleteCharacter()}
            >
              End Chronicle
            </button>
          </div>

          <section className="hero-card">
            <div>
              <p className="eyebrow">
                {character.race.name} · {character.alignment}
              </p>
              <h2>{character.name}</h2>
              <p>
                Level {character.level} {character.current_job.name} ·{" "}
                {character.current_location.name}
              </p>
            </div>
            <div className="resource-grid" aria-label="Character resources">
              <span>
                HP{" "}
                <strong>
                  {character.current_hp}/{character.derived_stats.max_hp}
                </strong>
              </span>
              <span>
                MP{" "}
                <strong>
                  {character.current_mp}/{character.derived_stats.max_mp}
                </strong>
              </span>
              <span>
                Stamina{" "}
                <strong>
                  {character.current_stamina}/
                  {character.derived_stats.max_stamina}
                </strong>
              </span>
            </div>
          </section>

          <section className="panel">
            <h3>Attributes</h3>
            <div className="stat-grid">
              {Object.entries(statLabels).map(([key, label]) => (
                <div key={key}>
                  <span>{label}</span>
                  <strong>
                    {character.stats[key as keyof typeof character.stats]}
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
                  <strong>{job.job.name}</strong> · Job level {job.job_level}
                  {job.active ? " · Active" : ""}
                </p>
              ))}
            </div>
            <div>
              <h3>Skills</h3>
              {character.skills.map((skill) => (
                <p key={skill.id}>
                  <strong>{skill.name}</strong> · Rank {skill.skill_level}
                </p>
              ))}
            </div>
          </section>

          <section className="panel split-panel">
            <div>
              <h3>Inventory</h3>
              <p className="muted">
                {inventory?.used_slots ?? 0}/{inventory?.slot_count ?? 0} slots
                · {inventory?.total_weight ?? 0}/{inventory?.max_weight ?? 0}{" "}
                weight
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
                    <span>{slot.name}</span> · {slot.item?.name ?? "Empty"}
                  </li>
                ))}
              </ul>
            </div>
          </section>

          <WorldPanel
            quests={quests}
            npcs={npcs}
            factions={factions}
            dungeons={dungeons}
            journal={journal}
            busy={busy}
            interactionText={interactionText}
            narrative={narrative}
            onQuestAction={(quest, action) => {
              void questAction(quest, action);
            }}
            onNpcAction={(npc, action) => {
              void npcAction(npc, action);
            }}
            onDialogue={(npc, topic) => {
              void dialogue(npc, topic);
            }}
            onQuestFraming={(quest) => {
              void questFraming(quest);
            }}
            onCloseNarrative={() => setNarrative(null)}
            onJoinFaction={(faction) => {
              void joinFaction(faction);
            }}
            onDungeonAction={(dungeon, action) => {
              void dungeonAction(dungeon, action);
            }}
          />

          <section className="panel">
            <h3>Encounters</h3>
            {encounters.length === 0 ? (
              <p className="muted">No combat encounters at this location.</p>
            ) : (
              <div className="encounter-grid">
                {encounters.map((encounter) => (
                  <article key={encounter.id}>
                    <p className="eyebrow">{encounter.difficulty}</p>
                    <h4>{encounter.name}</h4>
                    <p>
                      Level {encounter.monster_level} {encounter.monster_name}
                    </p>
                    <p className="muted">
                      {encounter.reward_experience} XP / {encounter.reward_gold}{" "}
                      gold
                    </p>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => void startCombat(encounter)}
                    >
                      Begin combat
                    </button>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="panel">
            <div className="section-heading">
              <h3>Known world</h3>
              <button
                type="button"
                disabled={busy}
                onClick={() => void describeLocation()}
              >
                Observe surroundings
              </button>
            </div>
            <div className="location-grid">
              {locations
                .filter((location) => location.discovered || location.reachable)
                .map((location) => (
                  <article key={location.id}>
                    <p className="eyebrow">Danger {location.danger_level}</p>
                    <h4>{location.name}</h4>
                    <p>{location.description}</p>
                    {location.reachable &&
                      location.id !== character.current_location.id && (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => void travel(location, character.id)}
                        >
                          Travel here
                        </button>
                      )}
                    {location.id === character.current_location.id && (
                      <span className="current">Current location</span>
                    )}
                  </article>
                ))}
            </div>
          </section>
          </div>
        ) : null}
      </ErrorBoundary>
    </main>
  );
};

export default App;
