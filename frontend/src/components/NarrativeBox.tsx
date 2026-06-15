import type { Narrative } from "../types/gameplay";

interface NarrativeBoxProps {
  narrative: Narrative;
  onClose: () => void;
}

const NarrativeBox = ({ narrative, onClose }: NarrativeBoxProps) => (
  <aside className="dialogue-box" aria-label="Story dialogue">
    <div className="narrative-speaker">
      {narrative.speaker_name ?? "Chronicle"}
    </div>

    <div className="dialogue-content">
      <div className="narrative-text typing-effect">
        {narrative.text}
      </div>
    </div>

    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem', borderTop: '1px solid #4a6fa5', paddingTop: '0.5rem' }}>
      <p className="muted" style={{ margin: 0, fontSize: '0.8rem' }}>
        {narrative.fallback_used && <span className="local-narrative danger" style={{ marginRight: '0.5rem' }}>[Offline Mode]</span>}
        Grounded in {narrative.context_memory_count} memories
        {narrative.cached ? " · Cached" : ""}
      </p>
      <button type="button" onClick={onClose}>
        Continue ▼
      </button>
    </div>
  </aside>
);

export default NarrativeBox;
