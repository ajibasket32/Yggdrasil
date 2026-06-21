import { useEffect, useRef } from "react";
import { Game, AUTO, Scale } from "phaser";
import WorldScene from "../scenes/WorldScene";
import CombatScene from "../scenes/CombatScene";
import type { PresentationLocation } from "../scenes/WorldScene";
import type {
  CombatState,
  Npc,
  Location,
  EncounterDefinition,
} from "../types/gameplay";

interface GameCanvasProps {
  mode: "EXPLORATION" | "COMBAT";
  locationName?: string;
  combatState?: CombatState | null;
  npcs?: Npc[];
  reachableLocations?: Location[];
  encounters?: EncounterDefinition[];
  presentationLocation?: PresentationLocation;
  onTravel?: (location: Location) => void;
  onInteract?: (npc: Npc) => void;
  onEncounter?: (encounter: EncounterDefinition) => void;
}

const GameCanvas = ({
  mode,
  locationName,
  combatState,
  npcs,
  reachableLocations,
  encounters,
  presentationLocation,
  onTravel,
  onInteract,
  onEncounter,
}: GameCanvasProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const gameRef = useRef<Game | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const config = {
      type: AUTO,
      width: window.innerWidth,
      height: window.innerHeight,
      parent: containerRef.current,
      scale: {
        mode: Scale.RESIZE,
        autoCenter: Scale.CENTER_BOTH,
      },
      scene: [WorldScene, CombatScene],
      backgroundColor: "#0a0c10",
      physics: {
        default: "arcade",
        arcade: {
          gravity: { x: 0, y: 0 },
          debug: false,
        },
      },
    };

    const game = new Game(config);
    gameRef.current = game;

    return () => {
      gameRef.current?.destroy(true);
      gameRef.current = null;
    };
  }, []);

  useEffect(() => {
    const game = gameRef.current;
    if (!game) return;

    // Listen for events from Phaser
    const handleTravel = (loc: Location) => onTravel?.(loc);
    const handleInteract = (npc: Npc) => onInteract?.(npc);
    const handleEncounter = (enc: EncounterDefinition) => onEncounter?.(enc);

    game.events.on("phaser-travel", handleTravel);
    game.events.on("phaser-interact", handleInteract);
    game.events.on("phaser-encounter", handleEncounter);

    return () => {
      game.events.off("phaser-travel", handleTravel);
      game.events.off("phaser-interact", handleInteract);
      game.events.off("phaser-encounter", handleEncounter);
    };
  }, [onTravel, onInteract, onEncounter]);

  useEffect(() => {
    if (!gameRef.current) return;

    if (locationName) {
      gameRef.current.registry.set("locationName", locationName);
    }
    if (combatState) {
      gameRef.current.registry.set("combatState", combatState);
    }
    if (npcs) {
      gameRef.current.registry.set("npcs", npcs);
    }
    if (reachableLocations) {
      gameRef.current.registry.set("reachableLocations", reachableLocations);
    }
    if (encounters) {
      gameRef.current.registry.set("encounters", encounters);
    }
    gameRef.current.registry.set("presentationLocation", presentationLocation);

    if (mode === "COMBAT") {
      if (gameRef.current.scene.isActive("WorldScene")) {
        gameRef.current.scene.stop("WorldScene");
      }
      if (!gameRef.current.scene.isActive("CombatScene")) {
        gameRef.current.scene.start("CombatScene");
      }
    } else {
      if (gameRef.current.scene.isActive("CombatScene")) {
        gameRef.current.scene.stop("CombatScene");
      }
      if (!gameRef.current.scene.isActive("WorldScene")) {
        gameRef.current.scene.start("WorldScene");
      }
    }
  }, [
    mode,
    locationName,
    combatState,
    npcs,
    reachableLocations,
    encounters,
    presentationLocation,
  ]);

  return <div ref={containerRef} className="game-canvas-container" />;
};

export default GameCanvas;
