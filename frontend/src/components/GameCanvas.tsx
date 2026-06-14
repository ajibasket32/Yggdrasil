import { useEffect, useRef } from "react";
import { Game, AUTO } from "phaser";
import WorldScene from "../scenes/WorldScene";
import CombatScene from "../scenes/CombatScene";

interface GameCanvasProps {
  mode: "EXPLORATION" | "COMBAT";
}

const GameCanvas = ({ mode }: GameCanvasProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const gameRef = useRef<Game | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const config = {
      type: AUTO,
      width: 800,
      height: 400,
      parent: containerRef.current,
      scene: [WorldScene, CombatScene],
    };

    gameRef.current = new Game(config);

    return () => {
      gameRef.current?.destroy(true);
      gameRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!gameRef.current) return;

    if (mode === "COMBAT") {
      gameRef.current.scene.start("CombatScene");
      gameRef.current.scene.stop("WorldScene");
    } else {
      gameRef.current.scene.start("WorldScene");
      gameRef.current.scene.stop("CombatScene");
    }
  }, [mode]);

  return <div ref={containerRef} className="game-canvas-container" />;
};

export default GameCanvas;
