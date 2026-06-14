import type { Narrative } from "../types/gameplay";

interface NarrativeBoxProps {
  narrative: Narrative;
  onClose: () => void;
}

const NarrativeBox = ({ narrative, onClose }: NarrativeBoxProps) => (
  <aside className="dialogue-box" aria-label="Story dialogue">
    <div className="dialogue-heading">
      <div>
        <p className="eyebrow">{narrative.tone}</p>
        <h4>{narrative.speaker_name ?? "Chronicle"}</h4>
      </div>
      {narrative.fallback_used && (
        <span className="local-narrative">Local narration</span>
      )}
    </div>
    <p>{narrative.text}</p>
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
