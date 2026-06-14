import type { Narrative } from "../types/gameplay";

interface NarrativeBoxProps {
  narrative: Narrative;
  onClose: () => void;
}

const NarrativeBox = ({ narrative, onClose }: NarrativeBoxProps) => (
  <aside className="dialogue-box kenney-panel" aria-label="Story dialogue">
    <div className="dialogue-heading">
      <div>
        <p className="eyebrow">{narrative.tone}</p>
        <h4>{narrative.speaker_name ?? "Chronicle"}</h4>
      </div>
      {narrative.fallback_used && (
        <span className="local-narrative">Local narration</span>
      )}
    </div>
    <div className="dialogue-content">
      <img
        src="assets/ui/rpg/iconCheck_beige.png"
        alt=""
        className="dialogue-icon"
      />
      <p>{narrative.text}</p>
    </div>
    <p className="dialogue-context">
      Grounded in {narrative.context_memory_count} relevant{" "}
      {narrative.context_memory_count === 1 ? "memory" : "memories"}
      {narrative.cached ? " · Reused safely" : ""}
    </p>
    <button type="button" onClick={onClose}>
      Continue
    </button>
  </aside>
);

export default NarrativeBox;
