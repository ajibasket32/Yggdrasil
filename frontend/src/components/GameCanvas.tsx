import { useEffect, useRef } from "react";
import { Game, AUTO, Scale } from "phaser";
import WorldScene from "../scenes/WorldScene";
import CombatScene from "../scenes/CombatScene";
import type { CombatState } from "../types/gameplay";

interface GameCanvasProps {
  mode: "EXPLORATION" | "COMBAT";
  locationName?: string;
  combatState?: CombatState | null;
}

const GameCanvas = ({ mode, locationName, combatState }: GameCanvasProps) => {
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
        autoCenter: Scale.CENTER_BOTH
      },
      scene: [WorldScene, CombatScene],
      backgroundColor: '#0a0c10',
    };

    gameRef.current = new Game(config);

    return () => {
      gameRef.current?.destroy(true);
      gameRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!gameRef.current) return;
    
    if (locationName) {
      gameRef.current.registry.set("locationName", locationName);
    }
    if (combatState) {
      gameRef.current.registry.set("combatState", combatState);
    }

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
  }, [mode, locationName, combatState]);

  return <div ref={containerRef} className="game-canvas-container" />;
};

export default GameCanvas;
