import { Scene } from "phaser";
import type { Npc, Location, EncounterDefinition } from "../types/gameplay";
import playerUrl from "../assets/characters/RPG_assets.png";
import {
  mapForLocation,
  markerPosition,
  type MarkerType,
  type WorldMapDefinition,
} from "../systems/worldMaps";

const PLAYER_IDLE_FRAME = 10;
const PLAYER_SPEED = 200;

declare global {
  interface Window {
    __YGGDRASIL_AUDIT__?: {
      world?: {
        playerX: number;
        playerY: number;
        moving: boolean;
        animation: string | null;
        mapId: string;
        musicKey: string;
        landmarks: string[];
      };
      combat?: unknown;
    };
  }
}

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
  private mapObjects!: Phaser.GameObjects.Group;
  private collisionObjects!: Phaser.Physics.Arcade.StaticGroup;
  private activeMap!: WorldMapDefinition;
  private mapWidth = 800;
  private mapHeight = 800;
  private auditEnabled = false;

  constructor() {
    super("WorldScene");
  }

  preload() {
    if (!this.textures.exists("player")) {
      this.load.spritesheet("player", playerUrl, {
        frameWidth: 16,
        frameHeight: 16,
      });
    }
  }

  create() {
    this.auditEnabled = window.location.search.includes("audit=1");
    this.mapObjects = this.add.group();
    this.collisionObjects = this.physics.add.staticGroup();
    this.activeMap = mapForLocation(this.registry.get("locationName"));
    this.mapWidth = this.activeMap.width;
    this.mapHeight = this.activeMap.height;
    this.physics.world.setBounds(0, 0, this.mapWidth, this.mapHeight);
    this.createMap();

    this.player = this.physics.add.sprite(
      this.activeMap.spawn.x,
      this.activeMap.spawn.y,
      "player",
      PLAYER_IDLE_FRAME,
    );
    this.player.setScale(3);
    this.player.setCollideWorldBounds(true);
    this.physics.add.collider(this.player, this.collisionObjects);
    this.createAnimations();

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
    this.updateAuditState(false);

    this.cameras.main.flash(500);
  }

  private createMap() {
    this.mapObjects.clear(true, true);
    this.collisionObjects.clear(true, true);

    const background = this.add
      .rectangle(
        this.mapWidth / 2,
        this.mapHeight / 2,
        this.mapWidth,
        this.mapHeight,
        this.activeMap.backgroundColor,
      )
      .setOrigin(0.5);
    this.mapObjects.add(background);

    [
      ...this.activeMap.terrain,
      ...this.activeMap.roads,
      ...this.activeMap.props,
    ].forEach((rect) => {
      const object = this.add
        .rectangle(
          rect.x,
          rect.y,
          rect.width,
          rect.height,
          rect.color,
          rect.alpha ?? 1,
        )
        .setOrigin(0.5);
      this.mapObjects.add(object);
      if (rect.collides) {
        this.physics.add.existing(object, true);
        this.collisionObjects.add(object);
      }
      if (rect.label) {
        this.addMapLabel(rect.label, rect.x, rect.y);
      }
    });

    this.activeMap.circles.forEach((circle) => {
      const object = this.add.circle(
        circle.x,
        circle.y,
        circle.radius,
        circle.color,
        circle.alpha ?? 1,
      );
      this.mapObjects.add(object);
      if (circle.collides) {
        this.physics.add.existing(object, true);
        this.collisionObjects.add(object);
      }
      if (circle.label) {
        this.addMapLabel(circle.label, circle.x, circle.y);
      }
    });
  }

  private addMapLabel(label: string, x: number, y: number) {
    const text = this.add
      .text(x, y - 12, label, {
        fontFamily: "monospace",
        fontSize: "13px",
        color: "#ffffff",
        stroke: "#111827",
        strokeThickness: 3,
      })
      .setOrigin(0.5);
    this.mapObjects.add(text);
  }

  private createAnimations() {
    if (!this.anims.exists("player-walk")) {
      this.anims.create({
        key: "player-walk",
        frames: this.anims.generateFrameNumbers("player", {
          start: 8,
          end: 11,
        }),
        frameRate: 8,
        repeat: -1,
      });
    }
  }

  private updateLocation() {
    const locName = this.registry.get("locationName") as string;
    if (locName && this.locationText) {
      this.locationText.setText(locName);
    }
    const nextMap = mapForLocation(locName);
    if (this.activeMap && this.activeMap.mapId !== nextMap.mapId) {
      this.activeMap = nextMap;
      this.mapWidth = nextMap.width;
      this.mapHeight = nextMap.height;
      this.physics.world.setBounds(0, 0, this.mapWidth, this.mapHeight);
      this.cameras.main.setBounds(0, 0, this.mapWidth, this.mapHeight);
      this.createMap();
      if (this.player) {
        this.player.setPosition(nextMap.spawn.x, nextMap.spawn.y);
      }
      this.refreshMarkers();
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
      const position = markerPosition(this.activeMap, "NPC", npc, i);
      this.addMarker(npc, "NPC", position.x, position.y);
    });

    encounters.forEach((enc, i) => {
      const position = markerPosition(this.activeMap, "ENCOUNTER", enc, i);
      this.addMarker(enc, "ENCOUNTER", position.x, position.y);
    });

    travel.forEach((loc, i) => {
      const position = markerPosition(this.activeMap, "TRAVEL", loc, i);
      this.addMarker(loc, "TRAVEL", position.x, position.y);
    });
  }

  private addMarker(data: any, type: MarkerType, x: number, y: number) {
    const markerTint =
      type === "NPC" ? 0x86efac : type === "ENCOUNTER" ? 0xf87171 : 0xfef08a;
    const sprite = this.add.sprite(x, y, "player", PLAYER_IDLE_FRAME);
    sprite.setScale(2.5);
    sprite.setTint(markerTint);
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

    body.setVelocity(0);

    if (this.cursors.left.isDown || this.wasd.A.isDown) {
      body.setVelocityX(-PLAYER_SPEED);
      this.player.setFlipX(true);
    } else if (this.cursors.right.isDown || this.wasd.D.isDown) {
      body.setVelocityX(PLAYER_SPEED);
      this.player.setFlipX(false);
    }

    if (this.cursors.up.isDown || this.wasd.W.isDown) {
      body.setVelocityY(-PLAYER_SPEED);
    } else if (this.cursors.down.isDown || this.wasd.S.isDown) {
      body.setVelocityY(PLAYER_SPEED);
    }

    body.velocity.normalize().scale(PLAYER_SPEED);
    const moving = body.velocity.x !== 0 || body.velocity.y !== 0;
    if (moving) {
      this.player.play("player-walk", true);
    } else {
      this.player.anims.stop();
      this.player.setFrame(PLAYER_IDLE_FRAME);
    }

    this.checkInteractions();
    this.updateAuditState(moving);
  }

  private updateAuditState(moving: boolean) {
    if (!this.auditEnabled) return;
    window.__YGGDRASIL_AUDIT__ = {
      ...(window.__YGGDRASIL_AUDIT__ ?? {}),
      world: {
        playerX: this.player.x,
        playerY: this.player.y,
        moving,
        animation: this.player.anims.currentAnim?.key ?? null,
        mapId: this.activeMap.mapId,
        musicKey: this.activeMap.musicKey,
        landmarks: this.activeMap.landmarks,
      },
    };
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
