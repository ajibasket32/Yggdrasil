import type {
  Dungeon,
  Faction,
  JournalEntry,
  Narrative,
  Npc,
  Quest,
  DialogueTopic,
} from "../types/gameplay";
import NarrativeBox from "./NarrativeBox";

interface WorldPanelProps {
  quests: Quest[];
  npcs: Npc[];
  factions: Faction[];
  dungeons: Dungeon[];
  journal: JournalEntry[];
  busy: boolean;
  interactionText: string | null;
  narrative: Narrative | null;
  onQuestAction: (
    quest: Quest,
    action: "accept" | "submit" | "fail" | "archive",
  ) => void;
  onNpcAction: (npc: Npc, action: "GREET" | "OFFER_HELP") => void;
  onDialogue: (npc: Npc, topic: DialogueTopic) => void;
  onQuestFraming: (quest: Quest) => void;
  onCloseNarrative: () => void;
  onJoinFaction: (faction: Faction) => void;
  onDungeonAction: (dungeon: Dungeon, action: "enter" | "clear") => void;
}

const WorldPanel = ({
  quests,
  npcs,
  factions,
  dungeons,
  journal,
  busy,
  interactionText,
  narrative,
  onQuestAction,
  onNpcAction,
  onDialogue,
  onQuestFraming,
  onCloseNarrative,
  onJoinFaction,
  onDungeonAction,
}: WorldPanelProps) => (
  <>
    <section className="panel">
      <h3>Quest journal</h3>
      {quests.length === 0 ? (
        <p className="muted">No available or recorded quests.</p>
      ) : (
        <div className="world-grid">
          {quests.map((quest) => (
            <article key={quest.id}>
              <p className="eyebrow">{quest.status}</p>
              <h4>{quest.title}</h4>
              <p>{quest.description}</p>
              <ol className="objective-list">
                {quest.steps.map((step) => (
                  <li key={step.id}>
                    {step.complete
                      ? "Complete"
                      : `${step.progress}/${step.required_count}`}
                    {" · "}
                    {step.description}
                  </li>
                ))}
              </ol>
              <p className="muted">
                {quest.rewards.experience} XP · {quest.rewards.gold} gold ·{" "}
                {quest.rewards.reputation} reputation
              </p>
              <div className="action-row">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onQuestFraming(quest)}
                >
                  Hear story
                </button>
                {quest.status === "NOT_STARTED" && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => onQuestAction(quest, "accept")}
                  >
                    Accept quest
                  </button>
                )}
                {quest.status === "ACTIVE" && quest.objectives_complete && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => onQuestAction(quest, "submit")}
                  >
                    Claim rewards
                  </button>
                )}
                {quest.status === "ACTIVE" && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => onQuestAction(quest, "fail")}
                  >
                    Abandon quest
                  </button>
                )}
                {(quest.status === "COMPLETED" ||
                  quest.status === "FAILED") && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => onQuestAction(quest, "archive")}
                  >
                    Archive
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>

    <section className="panel split-panel">
      <div>
        <h3>People nearby</h3>
        {npcs.length === 0 ? (
          <p className="muted">No NPCs are present.</p>
        ) : (
          npcs.map((npc) => (
            <article className="world-card" key={npc.id}>
              <h4>{npc.name}</h4>
              <p>{npc.occupation}</p>
              <div className="action-row">
                {npc.available_actions.map((action) => (
                  <button
                    type="button"
                    disabled={busy}
                    key={action}
                    onClick={() => onNpcAction(npc, action)}
                  >
                    {action === "GREET" ? "Greet" : "Offer help"}
                  </button>
                ))}
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onDialogue(npc, "GREETING")}
                >
                  Speak
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onDialogue(npc, "QUEST")}
                >
                  Ask about quest
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onDialogue(npc, "LOCAL_NEWS")}
                >
                  Ask local news
                </button>
              </div>
            </article>
          ))
        )}
        {interactionText !== null && (
          <p className="interaction-result" role="status">
            {interactionText}
          </p>
        )}
        {narrative !== null && (
          <NarrativeBox narrative={narrative} onClose={onCloseNarrative} />
        )}
      </div>
      <div>
        <h3>Factions</h3>
        {factions.map((faction) => (
          <article className="world-card" key={faction.id}>
            <h4>{faction.name}</h4>
            <p>{faction.description}</p>
            <p className="muted">
              {faction.rank} · Reputation {faction.reputation}
            </p>
            {!faction.joined && (
              <button
                type="button"
                disabled={busy}
                onClick={() => onJoinFaction(faction)}
              >
                Join faction
              </button>
            )}
          </article>
        ))}
      </div>
    </section>

    <section className="panel split-panel">
      <div>
        <h3>Dungeons</h3>
        {dungeons.length === 0 ? (
          <p className="muted">No dungeon is visible here.</p>
        ) : (
          dungeons.map((dungeon) => (
            <article className="world-card" key={dungeon.id}>
              <h4>{dungeon.name}</h4>
              <p>{dungeon.description}</p>
              <p className="muted">
                Recommended level {dungeon.recommended_level} · Boss{" "}
                {dungeon.boss_alive ? "alive" : "defeated"}
              </p>
              {!dungeon.entered && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onDungeonAction(dungeon, "enter")}
                >
                  Enter dungeon
                </button>
              )}
              {dungeon.entered && !dungeon.cleared && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onDungeonAction(dungeon, "clear")}
                >
                  Secure dungeon
                </button>
              )}
              {dungeon.cleared && (
                <span className="current">Permanently cleared</span>
              )}
            </article>
          ))
        )}
      </div>
      <div>
        <h3>Chronicle</h3>
        {journal.length === 0 ? (
          <p className="muted">No journal entries yet.</p>
        ) : (
          <ul>
            {journal.slice(-8).map((entry) => (
              <li key={entry.id}>
                <strong>{entry.title}</strong> · {entry.body}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  </>
);

export default WorldPanel;
