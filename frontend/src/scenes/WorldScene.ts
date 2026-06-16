import { Scene } from "phaser";
import type { Npc, Location, EncounterDefinition } from "../types/gameplay";

export default class WorldScene extends Scene {
  private player!: Phaser.Physics.Arcade.Sprite;
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private wasd!: {
    W: Phaser.Input.Keyboard.Key;
    A: Phaser.Input.Keyboard.Key;
    S: Phaser.Input.Keyboard.Key;
    D: Phaser.Input.Keyboard.Key;
    E: Phaser.Input.Keyboard.Key;
  };
  private locationText!: Phaser.GameObjects.Text;
  private interactionHint!: Phaser.GameObjects.Text;
  private markers: Phaser.GameObjects.Group | null = null;
  private mapWidth = 800;
  private mapHeight = 800;

  constructor() {
    super("WorldScene");
  }

  preload() {
    this.load.image("tiles", "assets/tilesets/world.png");
    this.load.spritesheet("player", "assets/characters/RPG_assets.png", {
      frameWidth: 16,
      frameHeight: 16,
    });
  }

  create() {
    this.physics.world.setBounds(0, 0, this.mapWidth, this.mapHeight);

    this.createBackground();

    const centerX = this.mapWidth / 2;
    const centerY = this.mapHeight / 2;
    this.player = this.physics.add.sprite(centerX, centerY, "player", 0);
    this.player.setScale(3);
    this.player.setCollideWorldBounds(true);

    this.cursors = this.input.keyboard!.createCursorKeys();
    this.wasd = this.input.keyboard!.addKeys("W,A,S,D,E") as any;

    this.cameras.main.setBounds(0, 0, this.mapWidth, this.mapHeight);
    this.cameras.main.startFollow(this.player, true, 0.1, 0.1);

    this.locationText = this.add
      .text(10, 10, "Unknown Location", {
        fontFamily: "'Press Start 2P', monospace",
        fontSize: "18px",
        color: "#fef08a",
        stroke: "#000",
        strokeThickness: 4,
      })
      .setScrollFactor(0);

    this.interactionHint = this.add
      .text(400, 500, "", {
        fontFamily: "'Press Start 2P', monospace",
        fontSize: "14px",
        color: "#ffffff",
        stroke: "#000",
        strokeThickness: 3,
      })
      .setOrigin(0.5)
      .setScrollFactor(0)
      .setVisible(false);

    this.markers = this.add.group();

    this.registry.events.on(
      "changedata-locationName",
      this.updateLocation,
      this,
    );
    this.registry.events.on("changedata-npcs", this.refreshMarkers, this);
    this.registry.events.on("changedata-encounters", this.refreshMarkers, this);
    this.registry.events.on(
      "changedata-reachableLocations",
      this.refreshMarkers,
      this,
    );

    this.updateLocation();
    this.refreshMarkers();

    this.cameras.main.flash(500);
  }

  private createBackground() {
    const bg = this.add.tileSprite(
      0,
      0,
      this.mapWidth,
      this.mapHeight,
      "tiles",
    );
    bg.setOrigin(0, 0);
    bg.setTileScale(3);
  }

  private updateLocation() {
    const locName = this.registry.get("locationName") as string;
    if (locName && this.locationText) {
      this.locationText.setText(locName);
    }
  }

  private refreshMarkers() {
    if (!this.markers) return;
    this.markers.clear(true, true);

    const npcs = (this.registry.get("npcs") as Npc[]) || [];
    const encounters =
      (this.registry.get("encounters") as EncounterDefinition[]) || [];
    const travel =
      (this.registry.get("reachableLocations") as Location[]) || [];

    npcs.forEach((npc, i) => {
      this.addMarker(npc, "NPC", 200, 200 + i * 100, 48);
    });

    encounters.forEach((enc, i) => {
      this.addMarker(enc, "ENCOUNTER", 600, 200 + i * 100, 56);
    });

    travel.forEach((loc, i) => {
      this.addMarker(loc, "TRAVEL", 400, 600 + i * 100, 32);
    });
  }

  private addMarker(
    data: any,
    type: "NPC" | "ENCOUNTER" | "TRAVEL",
    x: number,
    y: number,
    frame: number,
  ) {
    const sprite = this.add.sprite(x, y, "player", frame);
    sprite.setScale(2.5);
    (sprite as any).markerData = data;
    (sprite as any).markerType = type;
    this.markers?.add(sprite);

    const label = this.add
      .text(x, y - 40, data.name || (data as Location).name, {
        fontFamily: "monospace",
        fontSize: "12px",
        color: "#ffffff",
        stroke: "#000",
        strokeThickness: 2,
      })
      .setOrigin(0.5);
    this.markers?.add(label);
  }

  update() {
    if (!this.player || !this.player.body) return;
    const body = this.player.body as Phaser.Physics.Arcade.Body;

    const speed = 200;

    body.setVelocity(0);

    if (this.cursors.left.isDown || this.wasd.A.isDown) {
      body.setVelocityX(-speed);
      this.player.setFlipX(true);
    } else if (this.cursors.right.isDown || this.wasd.D.isDown) {
      body.setVelocityX(speed);
      this.player.setFlipX(false);
    }

    if (this.cursors.up.isDown || this.wasd.W.isDown) {
      body.setVelocityY(-speed);
    } else if (this.cursors.down.isDown || this.wasd.S.isDown) {
      body.setVelocityY(speed);
    }

    body.velocity.normalize().scale(speed);

    this.checkInteractions();
  }

  private checkInteractions() {
    let closestMarker: any = null;
    let minDistance = 60;

    this.markers?.getChildren().forEach((child: any) => {
      if (child.texture && child.texture.key === "player") {
        const dist = Phaser.Math.Distance.Between(
          this.player.x,
          this.player.y,
          child.x,
          child.y,
        );
        if (dist < minDistance) {
          closestMarker = child;
          minDistance = dist;
        }
      }
    });

    if (closestMarker) {
      const type = closestMarker.markerType;
      const data = closestMarker.markerData;
      let hint = "";
      if (type === "NPC") hint = `Press E to talk to ${data.name}`;
      if (type === "ENCOUNTER") hint = `Press E to fight ${data.name}`;
      if (type === "TRAVEL") hint = `Press E to travel to ${data.name}`;

      this.interactionHint.setText(hint).setVisible(true);

      if (Phaser.Input.Keyboard.JustDown(this.wasd.E)) {
        this.handleInteraction(type, data);
      }
    } else {
      this.interactionHint.setVisible(false);
    }
  }

  private handleInteraction(type: string, data: any) {
    if (type === "NPC") {
      this.game.events.emit("phaser-interact", data);
    } else if (type === "ENCOUNTER") {
      this.game.events.emit("phaser-encounter", data);
    } else if (type === "TRAVEL") {
      this.game.events.emit("phaser-travel", data);
    }
  }
}
