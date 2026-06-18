import type { Narrative } from "../types/gameplay";

interface NarrativeBoxProps {
  narrative: Narrative;
  onClose: () => void;
}

const NarrativeBox = ({ narrative, onClose }: NarrativeBoxProps) => (
  <aside
    className={`dialogue-box kenney-panel-beige ${narrative.fallback_used ? "offline" : ""}`}
    aria-label="Story dialogue"
  >
    <div
      className="narrative-speaker"
      style={{
        background: "#4a6fa5",
        color: "white",
        border: "none",
        top: "-25px",
        borderRadius: "0",
        padding: "4px 16px",
      }}
    >
      {narrative.speaker_name ?? "Chronicle"}
    </div>

    <div className="dialogue-content" style={{ padding: "10px" }}>
      <div
        className="narrative-text typing-effect"
        style={{ color: "#333", fontSize: "1.2rem", fontWeight: "500" }}
      >
        {narrative.text}
      </div>
    </div>

    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginTop: "1rem",
        borderTop: "2px solid rgba(0,0,0,0.1)",
        paddingTop: "1rem",
      }}
    >
      <p
        className="muted"
        style={{ margin: 0, fontSize: "0.75rem", color: "#666" }}
      >
        {narrative.fallback_used && (
          <span
            className="local-narrative"
            style={{
              marginRight: "0.5rem",
              color: "#b91c1c",
              fontWeight: "bold",
            }}
          >
            [OFFLINE]
          </span>
        )}
        Memories: {narrative.context_memory_count}
        {narrative.cached ? " · CACHED" : ""}
      </p>
      <button
        type="button"
        className="kenney-button"
        style={{ padding: "6px 16px", fontSize: "0.8rem" }}
        onClick={onClose}
      >
        Continue ▼
      </button>
    </div>
  </aside>
);

export default NarrativeBox;
