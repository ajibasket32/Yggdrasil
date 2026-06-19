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
  onShopOpen?: (shopId: string) => void;
  onInnRest?: (npcId: string) => void;
  characterGold?: number;
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
  onShopOpen,
  onInnRest,
  characterGold = 0,
}: WorldPanelProps) => (
  <div className="world-panel-container">
    <section className="kenney-panel">
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <h3>Quest Journal</h3>
        <div className="controls-hint">
          <span className="eyebrow">Controls:</span> WASD Move · E Interact
        </div>
      </div>
      {quests.length === 0 ? (
        <p className="muted">
          No active or available quests. Explore to find more!
        </p>
      ) : (
        <div className="quest-list">
          {quests.map((quest) => (
            <article
              key={quest.id}
              className={`quest-card ${quest.status.toLowerCase()}`}
              style={{
                borderLeft:
                  quest.status === "ACTIVE"
                    ? "4px solid #fef08a"
                    : quest.status === "COMPLETED"
                      ? "4px solid #86efac"
                      : "4px solid #4a6fa5",
                paddingLeft: "1rem",
                marginBottom: "1.5rem",
                background: "rgba(0,0,0,0.2)",
                padding: "1rem",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <h4 style={{ margin: 0 }}>{quest.title}</h4>
                <span
                  className="eyebrow"
                  style={{
                    color:
                      quest.status === "ACTIVE"
                        ? "#fef08a"
                        : quest.status === "COMPLETED"
                          ? "#86efac"
                          : "#94a3b8",
                  }}
                >
                  {quest.status.replace("_", " ")}
                </span>
              </div>
              <p style={{ fontSize: "0.9rem", marginTop: "0.5rem" }}>
                {quest.description}
              </p>

              <div className="quest-objectives">
                <p className="eyebrow" style={{ fontSize: "0.7rem" }}>
                  Objectives
                </p>
                <ul style={{ listStyle: "none", padding: 0 }}>
                  {quest.steps.map((step) => (
                    <li
                      key={step.id}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        color: step.complete ? "#86efac" : "#fff",
                        textDecoration: step.complete ? "line-through" : "none",
                        fontSize: "0.85rem",
                      }}
                    >
                      <span>{step.complete ? "☑" : "☐"}</span>
                      <span>{step.description}</span>
                      <span className="muted" style={{ marginLeft: "auto" }}>
                        {step.progress}/{step.required_count}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>

              <div
                className="quest-rewards"
                style={{
                  marginTop: "1rem",
                  padding: "0.5rem",
                  background: "rgba(0,0,0,0.3)",
                  borderRadius: "4px",
                }}
              >
                <p
                  className="eyebrow"
                  style={{ fontSize: "0.7rem", margin: 0 }}
                >
                  Potential Rewards
                </p>
                <div
                  style={{
                    display: "flex",
                    gap: "1rem",
                    fontSize: "0.8rem",
                    color: "#fef08a",
                  }}
                >
                  <span>💰 {quest.rewards.gold}g</span>
                  <span>⭐ {quest.rewards.experience} XP</span>
                  {quest.rewards.reputation > 0 && (
                    <span>🛡️ {quest.rewards.reputation} Rep</span>
                  )}
                </div>
              </div>
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

    <section
      className="kenney-panel split-panel"
      style={{ marginTop: "1.5rem" }}
    >
      <div>
        <h3>People nearby</h3>
        {npcs.length === 0 ? (
          <p className="muted">No NPCs are present.</p>
        ) : (
          npcs.map((npc) => (
            <article className="grid-card" key={npc.id}>
              <h4>{npc.name}</h4>
              <p>{npc.occupation}</p>
              <div className="action-row">
                {npc.available_actions.map((action) => {
                  if (action === "GREET") {
                    return (
                      <button
                        type="button"
                        disabled={busy}
                        key={action}
                        onClick={() => onNpcAction(npc, action)}
                      >
                        Greet
                      </button>
                    );
                  }
                  if (action === "OFFER_HELP") {
                    return (
                      <button
                        type="button"
                        disabled={busy}
                        key={action}
                        onClick={() => onNpcAction(npc, action)}
                      >
                        Offer help
                      </button>
                    );
                  }
                  if (action === "SHOP" && npc.shop_id && onShopOpen) {
                    return (
                      <button
                        type="button"
                        disabled={busy}
                        key={action}
                        className="current"
                        onClick={() => onShopOpen(npc.shop_id!)}
                      >
                        Browse Shop
                      </button>
                    );
                  }
                  if (action === "REST" && onInnRest) {
                    const canAfford = characterGold >= 50;
                    return (
                      <button
                        type="button"
                        disabled={busy || !canAfford}
                        key={action}
                        className={canAfford ? "current" : "disabled"}
                        onClick={() => onInnRest(npc.id)}
                      >
                        {canAfford ? "Rest (50g)" : "Rest (Needs 50g)"}
                      </button>
                    );
                  }
                  return null;
                })}
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
          <article className="grid-card" key={faction.id}>
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

    <section
      className="kenney-panel split-panel"
      style={{ marginTop: "1.5rem", marginBottom: "4rem" }}
    >
      <div>
        <h3>Dungeons</h3>
        {dungeons.length === 0 ? (
          <p className="muted">No dungeon is visible here.</p>
        ) : (
          dungeons.map((dungeon) => (
            <article className="grid-card" key={dungeon.id}>
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
  </div>
);

export default WorldPanel;
