import type { EncounterDefinition, Location, Npc } from "../../types/gameplay";

interface GameCanvasMockProps {
  reachableLocations?: Location[];
  npcs?: Npc[];
  encounters?: EncounterDefinition[];
  onTravel?: (location: Location) => void;
  onInteract?: (npc: Npc) => void;
  onEncounter?: (encounter: EncounterDefinition) => void;
}

const GameCanvas = ({
  reachableLocations = [],
  npcs = [],
  encounters = [],
  onTravel,
  onInteract,
  onEncounter,
}: GameCanvasMockProps) => {
  const travelLocation = reachableLocations[0];
  const npc = npcs[0];
  const encounter = encounters[0];

  return (
    <div data-testid="game-canvas">
      {travelLocation && onTravel && (
        <button type="button" onClick={() => onTravel(travelLocation)}>
          Canvas Travel Marker
        </button>
      )}
      {npc && onInteract && (
        <button type="button" onClick={() => onInteract(npc)}>
          Canvas NPC Marker
        </button>
      )}
      {encounter && onEncounter && (
        <button type="button" onClick={() => onEncounter(encounter)}>
          Canvas Encounter Marker
        </button>
      )}
    </div>
  );
};

export default GameCanvas;
