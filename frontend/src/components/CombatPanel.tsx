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
    <div className="combat-resource">
      <span>
        {label} {current}/{maximum}
      </span>
      <div className="bar-track">
        <div className="bar-value" style={{ width: `${width}%` }} />
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
    <section className="combat-shell" aria-label="Combat encounter">
      <header className="combat-heading">
        <div>
          <p className="eyebrow">Round {combat.round_number}</p>
          <h2>{combat.encounter_name}</h2>
        </div>
        <strong
          className={`combat-status status-${combat.status.toLowerCase()}`}
        >
          {combat.status}
        </strong>
      </header>

      <div className="combatants">
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
        <div className="combat-actions" aria-label="Combat actions">
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
              {skill.name} ({skill.mana_cost} MP)
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
              {potion.name} x{potion.quantity}
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
            Escape
          </button>
        </div>
      ) : (
        <div className="combat-result">
          {combat.status === "VICTORY" && (
            <p>
              Gained {combat.rewards.experience} XP and {combat.rewards.gold}{" "}
              gold
              {combat.rewards.items.length > 0
                ? `. Loot: ${combat.rewards.items.join(", ")}.`
                : "."}
            </p>
          )}
          {combat.status === "DEFEAT" && (
            <p>The party was defeated. The character returns with 1 HP.</p>
          )}
          {combat.status === "FLED" && <p>The party escaped the encounter.</p>}
          <button type="button" disabled={busy} onClick={onReturn}>
            Return to archive
          </button>
        </div>
      )}

      <div className="combat-log" aria-live="polite">
        <h3>Combat log</h3>
        <ol>
          {combat.recent_log.map((entry) => (
            <li key={entry.id}>
              <span>Round {entry.round_number}</span>
              {entry.text}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
};

export default CombatPanel;
