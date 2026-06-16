import type {
  CombatActionType,
  CombatState,
  Inventory,
  Skill,
} from "../types/gameplay";

interface CombatPanelProps {
  combat: CombatState;
  skills: Skill[];
  inventory: Inventory | null;
  busy: boolean;
  onAction: (
    action: CombatActionType,
    skillId?: string,
    inventoryItemId?: string,
  ) => void;
  onFlee: () => void;
  onReturn: () => void;
}

const ResourceBar = ({
  label,
  current,
  maximum,
}: {
  label: string;
  current: number;
  maximum: number;
}) => {
  const width = maximum > 0 ? Math.max(0, (current / maximum) * 100) : 0;
  return (
    <div className="resource-bar-container">
      <span className="resource-bar-label">{label}</span>
      <div className="resource-bar">
        <div
          className={`resource-fill ${label.toLowerCase()}`}
          style={{ width: `${width}%` }}
        />
        <span className="resource-text">
          {current}/{maximum}
        </span>
      </div>
    </div>
  );
};

const CombatPanel = ({
  combat,
  skills,
  inventory,
  busy,
  onAction,
  onFlee,
  onReturn,
}: CombatPanelProps) => {
  const player = combat.participants.find((value) => value.side === "PLAYER");
  const enemy = combat.participants.find((value) => value.side === "ENEMY");
  const potion = inventory?.items.find(
    (item) => item.item_type === "CONSUMABLE" && item.quantity > 0,
  );
  const activeSkills = skills.filter((skill) => skill.skill_type === "ACTIVE");

  if (player === undefined || enemy === undefined) {
    return <section className="panel">Combat state is incomplete.</section>;
  }

  return (
    <section
      className="combat-shell"
      aria-label="Combat encounter"
      style={{
        position: "absolute",
        bottom: "1rem",
        left: "1rem",
        right: "1rem",
        display: "flex",
        gap: "1rem",
        alignItems: "flex-end",
      }}
    >
      <div
        className="combat-log-container jrpg-panel"
        style={{ flexGrow: 1, minWidth: "300px" }}
        aria-live="polite"
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginBottom: "0.5rem",
          }}
        >
          <span className="eyebrow">
            Round {combat.round_number} - {combat.encounter_name}
          </span>
          <strong
            className={
              combat.status === "ACTIVE"
                ? "success"
                : combat.status === "DEFEAT"
                  ? "danger"
                  : "success"
            }
          >
            {combat.status}
          </strong>
        </div>
        <ol style={{ padding: 0, margin: 0, listStyle: "none" }}>
          {combat.recent_log
            .slice()
            .reverse()
            .map((entry) => (
              <li key={entry.id}>
                <span>[{entry.round_number}]</span>
                <span style={{ color: "#e2e8f0" }}>{entry.text}</span>
              </li>
            ))}
        </ol>
      </div>

      <div className="combatants" style={{ display: "none" }}>
        {/* We hide the old combatants block since GameCanvas now renders HP bars, but we keep it in DOM for screen readers if needed */}
        {[player, enemy].map((participant) => (
          <article key={participant.id} className="combatant-card">
            <p className="eyebrow">{participant.side}</p>
            <h3>{participant.name}</h3>
            <ResourceBar
              label="HP"
              current={participant.current_hp}
              maximum={participant.max_hp}
            />
            <ResourceBar
              label="MP"
              current={participant.current_mp}
              maximum={participant.max_mp}
            />
            {participant.statuses.length > 0 && (
              <p className="status-list">
                {participant.statuses
                  .map((status) => `${status.code} (${status.duration})`)
                  .join(", ")}
              </p>
            )}
          </article>
        ))}
      </div>

      {combat.status === "ACTIVE" ? (
        <div
          className="action-bar jrpg-panel"
          aria-label="Combat actions"
          style={{ position: "static", width: "250px" }}
        >
          <button
            type="button"
            disabled={busy}
            onClick={() => onAction("ATTACK")}
          >
            Attack
          </button>
          {activeSkills.map((skill) => (
            <button
              key={skill.id}
              type="button"
              disabled={busy || player.current_mp < skill.mana_cost}
              onClick={() => onAction("SKILL", skill.id)}
            >
              {skill.name}{" "}
              <span style={{ fontSize: "0.8rem", color: "#89b4fa" }}>
                ({skill.mana_cost}MP)
              </span>
            </button>
          ))}
          {potion !== undefined && (
            <button
              type="button"
              disabled={busy}
              onClick={() =>
                onAction("ITEM", undefined, potion.inventory_item_id)
              }
            >
              Item{" "}
              <span style={{ fontSize: "0.8rem", color: "#89b4fa" }}>
                (x{potion.quantity})
              </span>
            </button>
          )}
          <button
            type="button"
            disabled={busy}
            onClick={() => onAction("GUARD")}
          >
            Guard
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => onAction("WAIT")}
          >
            Wait
          </button>
          <button type="button" disabled={busy} onClick={onFlee}>
            Flee
          </button>
        </div>
      ) : (
        <div className="jrpg-panel" style={{ width: "250px" }}>
          {combat.status === "VICTORY" && (
            <p className="success" style={{ fontSize: "0.9rem" }}>
              Victory! +{combat.rewards.experience} XP, +{combat.rewards.gold}{" "}
              Gold.
              {combat.rewards.items.length > 0
                ? ` Loot: ${combat.rewards.items.join(", ")}`
                : ""}
            </p>
          )}
          {combat.status === "DEFEAT" && (
            <p className="danger" style={{ fontSize: "0.9rem" }}>
              The party was defeated...
            </p>
          )}
          {combat.status === "FLED" && (
            <p style={{ fontSize: "0.9rem" }}>Escaped!</p>
          )}
          <button
            type="button"
            disabled={busy}
            onClick={onReturn}
            style={{ width: "100%", marginTop: "0.5rem" }}
          >
            Continue
          </button>
        </div>
      )}
    </section>
  );
};

export default CombatPanel;
