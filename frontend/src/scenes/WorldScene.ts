import { Scene } from "phaser";
import type { Npc, Location, EncounterDefinition } from "../types/gameplay";
import { GAMEPLAY_TUNING } from "../config/gameplayTuning";
import tilesUrl from "../assets/tilesets/world.png";
import playerUrl from "../assets/characters/RPG_assets.png";

const PLAYER_IDLE_FRAME = 10;
const PLAYER_SPEED = GAMEPLAY_TUNING.playerSpeed;
const INTERACTION_RADIUS = GAMEPLAY_TUNING.interactionRadius;

export type PresentationLocation = "BLACKSMITH" | "INN" | null;

type MarkerType = "NPC" | "ENCOUNTER" | "TRAVEL";

interface MapProfile {
  key: string;
  title: string;
  width: number;
  height: number;
  colors: {
    ground: number;
    path: number;
    trim: number;
    water?: number;
    shadow: number;
  };
  spawn: { x: number; y: number };
  musicKey: "city" | "interior" | "outskirts" | "forest";
  combatBackgroundKey: "city_gate" | "forest";
}

interface MarkerPosition {
  x: number;
  y: number;
}

declare global {
  interface Window {
    __YGGDRASIL_AUDIT__?: {
      world?: {
        playerX: number;
        playerY: number;
        moving: boolean;
        animation: string | null;
        location: string;
        musicKey: string;
        combatBackgroundKey: string;
        nearbyPrompt: string | null;
        interactionState: string;
        movementSpeed: number;
      };
      combat?: unknown;
      audio?: {
        bgmKey: string;
        muted: boolean;
        volume: number;
        ready: boolean;
        paused: boolean | null;
      };
      movePlayerTo?: (x: number, y: number) => void;
    };
  }
}

const MAPS = {
  city: {
    key: "city",
    title: "Valeris City",
    width: 1600,
    height: 960,
    colors: {
      ground: 0x4f8f5a,
      path: 0xbfa36c,
      trim: 0x6b4f2a,
      water: 0x3b82a0,
      shadow: 0x24351f,
    },
    spawn: { x: 780, y: 560 },
    musicKey: "city",
    combatBackgroundKey: "city_gate",
  },
  outskirts: {
    key: "outskirts",
    title: "Valeris Outskirts",
    width: 1700,
    height: 1000,
    colors: {
      ground: 0x6fa35a,
      path: 0x9a7443,
      trim: 0x5a4426,
      shadow: 0x314821,
    },
    spawn: { x: 260, y: 520 },
    musicKey: "outskirts",
    combatBackgroundKey: "forest",
  },
  greenwood: {
    key: "greenwood",
    title: "Greenwood Verge",
    width: 1700,
    height: 1000,
    colors: {
      ground: 0x386b3c,
      path: 0x7b5f32,
      trim: 0x23351f,
      shadow: 0x162416,
    },
    spawn: { x: 300, y: 560 },
    musicKey: "forest",
    combatBackgroundKey: "forest",
  },
  sylvan: {
    key: "sylvan",
    title: "Sylvan Branch",
    width: 1700,
    height: 1000,
    colors: {
      ground: 0x224d35,
      path: 0x5f4d34,
      trim: 0x14261c,
      water: 0x1e4f5a,
      shadow: 0x0d1b13,
    },
    spawn: { x: 280, y: 640 },
    musicKey: "forest",
    combatBackgroundKey: "forest",
  },
  blacksmith: {
    key: "blacksmith",
    title: "Blacksmith Interior",
    width: 1366,
    height: 768,
    colors: {
      ground: 0x5a4636,
      path: 0x7c5c3a,
      trim: 0x2f241c,
      shadow: 0x1b1410,
    },
    spawn: { x: 680, y: 520 },
    musicKey: "interior",
    combatBackgroundKey: "city_gate",
  },
  inn: {
    key: "inn",
    title: "Inn Interior",
    width: 1366,
    height: 768,
    colors: {
      ground: 0x574a3f,
      path: 0x8a6544,
      trim: 0x2f261f,
      shadow: 0x19130f,
    },
    spawn: { x: 700, y: 540 },
    musicKey: "interior",
    combatBackgroundKey: "city_gate",
  },
} satisfies Record<string, MapProfile>;

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
  private mapLayer: Phaser.GameObjects.Group | null = null;
  private mapWidth = MAPS.city.width;
  private mapHeight = MAPS.city.height;
  private auditEnabled = false;
  private currentProfile: MapProfile = MAPS.city;
  private nearbyPrompt: string | null = null;
  private interactionState:
    | "exploring"
    | "nearby_npc"
    | "interacting"
    | "service_overlay"
    | "returning_to_exploration" = "exploring";

  constructor() {
    super("WorldScene");
  }

  preload() {
    if (!this.textures.exists("tiles")) {
      this.load.image("tiles", tilesUrl);
    }
    if (!this.textures.exists("player")) {
      this.load.spritesheet("player", playerUrl, {
        frameWidth: 16,
        frameHeight: 16,
      });
    }
  }

  create() {
    this.auditEnabled = window.location.search.includes("audit=1");
    this.mapLayer = this.add.group();
    this.markers = this.add.group();

    this.currentProfile = this.resolveProfile();
    this.applyWorldBounds();
    this.createBackground();

    this.player = this.physics.add.sprite(
      this.currentProfile.spawn.x,
      this.currentProfile.spawn.y,
      "player",
      PLAYER_IDLE_FRAME,
    );
    this.player.setScale(3);
    this.player.setCollideWorldBounds(true);
    this.player.setDepth(this.player.y);
    this.createAnimations();

    this.cursors = this.input.keyboard!.createCursorKeys();
    this.wasd = this.input.keyboard!.addKeys("W,A,S,D,E") as any;

    this.cameras.main.startFollow(this.player, true, 0.1, 0.1);

    this.locationText = this.add
      .text(10, 10, this.currentProfile.title, {
        fontFamily: "'Press Start 2P', monospace",
        fontSize: "18px",
        color: "#fef08a",
        stroke: "#000",
        strokeThickness: 4,
      })
      .setScrollFactor(0)
      .setDepth(5000);

    this.interactionHint = this.add
      .text(683, 690, "", {
        fontFamily: "'Press Start 2P', monospace",
        fontSize: "14px",
        color: "#ffffff",
        stroke: "#000",
        strokeThickness: 3,
      })
      .setOrigin(0.5)
      .setScrollFactor(0)
      .setVisible(false)
      .setDepth(5000);

    this.registry.events.on(
      "changedata-locationName",
      this.updateLocation,
      this,
    );
    this.registry.events.on(
      "changedata-presentationLocation",
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
    this.installAuditHelpers();
    this.updateAuditState(false);
  }

  private installAuditHelpers() {
    if (!this.auditEnabled) return;
    window.__YGGDRASIL_AUDIT__ = {
      ...(window.__YGGDRASIL_AUDIT__ ?? {}),
      movePlayerTo: (x: number, y: number) => {
        this.player.setPosition(x, y);
        this.checkInteractions();
        this.updateAuditState(false);
      },
    };
  }

  private resolveProfile(): MapProfile {
    const focus = this.registry.get(
      "presentationLocation",
    ) as PresentationLocation;
    if (focus === "BLACKSMITH") return MAPS.blacksmith;
    if (focus === "INN") return MAPS.inn;

    const locationName = ((this.registry.get("locationName") as string) ?? "")
      .toLowerCase()
      .trim();
    if (locationName.includes("sylvan")) return MAPS.sylvan;
    if (locationName.includes("greenwood")) return MAPS.greenwood;
    if (locationName.includes("outskirts")) return MAPS.outskirts;
    return MAPS.city;
  }

  private updateLocation() {
    const nextProfile = this.resolveProfile();
    const changed = nextProfile.key !== this.currentProfile.key;
    this.currentProfile = nextProfile;

    if (changed) {
      this.applyWorldBounds();
      this.createBackground();
      if (this.player) {
        this.player.setPosition(nextProfile.spawn.x, nextProfile.spawn.y);
      }
      this.refreshMarkers();
    }

    if (this.locationText) {
      this.locationText.setText(nextProfile.title);
    }
  }

  private applyWorldBounds() {
    this.mapWidth = this.currentProfile.width;
    this.mapHeight = this.currentProfile.height;
    this.physics.world.setBounds(0, 0, this.mapWidth, this.mapHeight);
    this.cameras.main.setBounds(0, 0, this.mapWidth, this.mapHeight);
  }

  private createBackground() {
    this.mapLayer?.clear(true, true);
    const profile = this.currentProfile;

    const base = this.add.tileSprite(
      0,
      0,
      this.mapWidth,
      this.mapHeight,
      "tiles",
    );
    base.setOrigin(0, 0);
    base.setTileScale(3);
    base.setTint(profile.colors.ground);
    base.setDepth(-100);
    this.mapLayer?.add(base);

    const graphics = this.add.graphics();
    graphics.fillStyle(profile.colors.ground, 1);
    graphics.fillRect(0, 0, this.mapWidth, this.mapHeight);
    this.mapLayer?.add(graphics);

    if (profile.key === "blacksmith") {
      this.drawBlacksmith(graphics);
    } else if (profile.key === "inn") {
      this.drawInn(graphics);
    } else if (profile.key === "city") {
      this.drawCity(graphics);
    } else if (profile.key === "outskirts") {
      this.drawOutskirts(graphics);
    } else {
      this.drawForest(graphics, profile.key === "sylvan");
    }
  }

  private drawCity(graphics: Phaser.GameObjects.Graphics) {
    const { path, trim, shadow, water } = this.currentProfile.colors;
    this.rect(graphics, 0, 470, 1600, 120, path);
    this.rect(graphics, 720, 0, 140, 960, path);
    this.rect(graphics, 595, 360, 390, 250, 0x8c7650);
    this.rect(graphics, 560, 325, 460, 50, trim);
    this.rect(graphics, 1040, 80, 360, 220, water ?? 0x315f78);
    this.rect(graphics, 980, 250, 230, 190, 0x3f3022);
    this.rect(graphics, 1015, 280, 170, 125, 0x6c4027);
    this.rect(graphics, 360, 240, 260, 180, 0x664126);
    this.rect(graphics, 395, 275, 190, 110, 0x9b6b37);
    this.rect(graphics, 675, 120, 250, 150, 0x5d4961);
    this.rect(graphics, 710, 155, 180, 95, 0x9271a4);
    this.rect(graphics, 720, 690, 180, 210, shadow);
    this.rect(graphics, 760, 710, 100, 150, 0x72543c);
    this.rect(graphics, 370, 400, 240, 28, 0x3b2a1c);
    this.rect(graphics, 405, 420, 70, 40, 0x2b211a);
    this.rect(graphics, 705, 250, 205, 25, 0x3b2a1c);
    this.rect(graphics, 790, 245, 42, 45, 0x261b14);
    this.rect(graphics, 615, 430, 350, 40, 0xa8844f);
    this.rect(graphics, 1525, 455, 75, 160, 0x3e2d1f);
    this.rect(graphics, 0, 455, 75, 160, 0x3e2d1f);
    this.rect(graphics, 690, 520, 200, 70, 0xd1b16d);
    this.drawTrees(graphics, [
      [160, 190],
      [250, 260],
      [1450, 450],
      [1300, 760],
      [210, 720],
    ]);
  }

  private drawBlacksmith(graphics: Phaser.GameObjects.Graphics) {
    const { path, trim, shadow } = this.currentProfile.colors;
    this.rect(graphics, 120, 120, 1120, 560, trim);
    this.rect(graphics, 160, 160, 1040, 480, 0x6b523c);
    this.rect(graphics, 250, 230, 260, 210, 0x2c221b);
    this.rect(graphics, 295, 270, 170, 115, 0xd97732);
    this.rect(graphics, 590, 250, 500, 80, path);
    this.rect(graphics, 600, 350, 340, 120, shadow);
    this.rect(graphics, 980, 390, 120, 170, 0x8a5c32);
    this.rect(graphics, 260, 510, 310, 70, 0x92704c);
    this.rect(graphics, 720, 555, 180, 70, 0x2b211a);
    this.rect(graphics, 385, 365, 90, 35, 0xf97316);
    this.rect(graphics, 645, 370, 260, 30, 0xb7793a);
    this.rect(graphics, 650, 405, 70, 90, 0x1f2933);
    this.rect(graphics, 965, 365, 150, 30, 0x2b211a);
  }

  private drawInn(graphics: Phaser.GameObjects.Graphics) {
    const { path, trim, shadow } = this.currentProfile.colors;
    this.rect(graphics, 120, 120, 1120, 560, trim);
    this.rect(graphics, 160, 160, 1040, 480, 0x715a45);
    this.rect(graphics, 240, 210, 250, 90, 0x9b7651);
    this.rect(graphics, 240, 340, 250, 90, 0x9b7651);
    this.rect(graphics, 900, 210, 250, 90, 0x9b7651);
    this.rect(graphics, 900, 340, 250, 90, 0x9b7651);
    this.rect(graphics, 540, 230, 250, 150, path);
    this.rect(graphics, 600, 440, 240, 90, shadow);
    this.rect(graphics, 610, 565, 180, 60, 0x2b211a);
    this.rect(graphics, 1010, 510, 110, 110, 0xb4532b);
    this.rect(graphics, 560, 205, 300, 35, 0x4b3527);
    this.rect(graphics, 525, 395, 360, 40, 0xa47a4f);
    this.rect(graphics, 995, 485, 140, 30, 0xf97316);
  }

  private drawOutskirts(graphics: Phaser.GameObjects.Graphics) {
    const { path, trim, shadow } = this.currentProfile.colors;
    this.rect(graphics, 0, 475, 1700, 110, path);
    this.rect(graphics, 180, 330, 140, 300, 0x5f6f3a);
    this.rect(graphics, 240, 360, 1150, 45, trim);
    this.rect(graphics, 240, 650, 950, 45, trim);
    this.rect(graphics, 120, 360, 190, 280, shadow);
    this.rect(graphics, 560, 260, 120, 90, 0x8a7a56);
    this.rect(graphics, 950, 680, 120, 90, 0x8a7a56);
    this.rect(graphics, 0, 395, 210, 170, 0x4a2f1f);
    this.rect(graphics, 210, 415, 120, 130, 0x6b4f2a);
    this.rect(graphics, 330, 512, 940, 26, 0xc09a5a);
    this.rect(graphics, 740, 705, 210, 32, 0x4a2f1f);
    this.drawTrees(graphics, [
      [1180, 230],
      [1320, 310],
      [1470, 480],
      [1280, 735],
      [1510, 810],
    ]);
  }

  private drawForest(graphics: Phaser.GameObjects.Graphics, dense: boolean) {
    const { path, trim, shadow, water } = this.currentProfile.colors;
    this.rect(graphics, 0, 540, 1700, 95, path);
    this.rect(graphics, 420, 370, 180, 360, path);
    this.rect(graphics, 880, 250, 170, 470, path);
    if (water) this.rect(graphics, 1130, 120, 190, 760, water);
    this.rect(graphics, 650, 455, 130, 75, trim);
    this.rect(graphics, 1370, 590, 160, 130, trim);
    this.rect(graphics, 55, 505, 220, 30, 0x4a2f1f);
    this.rect(graphics, 410, 655, 360, 24, 0x4a2f1f);
    this.rect(graphics, 900, 330, 180, 22, 0x4a2f1f);
    this.drawTrees(graphics, [
      [130, 180],
      [230, 320],
      [330, 760],
      [710, 210],
      [780, 770],
      [1090, 370],
      [1330, 260],
      [1490, 430],
      [1560, 760],
    ]);
    if (dense) {
      this.rect(graphics, 0, 0, 1700, 95, shadow);
      this.rect(graphics, 0, 905, 1700, 95, shadow);
      this.rect(graphics, 0, 0, 95, 1000, shadow);
      this.rect(graphics, 1605, 0, 95, 1000, shadow);
    }
  }

  private drawTrees(
    graphics: Phaser.GameObjects.Graphics,
    trees: [number, number][],
  ) {
    trees.forEach(([x, y]) => {
      this.rect(graphics, x - 18, y + 28, 36, 45, 0x4a2f1f);
      this.rect(graphics, x - 48, y - 30, 96, 80, 0x1f5c33);
      this.rect(graphics, x - 30, y - 58, 60, 60, 0x2f7d43);
    });
  }

  private rect(
    graphics: Phaser.GameObjects.Graphics,
    x: number,
    y: number,
    width: number,
    height: number,
    color: number,
  ) {
    graphics.fillStyle(color, 1);
    graphics.fillRect(x, y, width, height);
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

  private refreshMarkers() {
    if (!this.markers) return;
    this.markers.clear(true, true);

    const npcs = (this.registry.get("npcs") as Npc[]) || [];
    const encounters =
      (this.registry.get("encounters") as EncounterDefinition[]) || [];
    const travel =
      (this.registry.get("reachableLocations") as Location[]) || [];

    npcs.forEach((npc, index) => {
      this.addMarker(npc, "NPC", this.markerPosition("NPC", npc.name, index));
    });

    encounters.forEach((encounter, index) => {
      this.addMarker(
        encounter,
        "ENCOUNTER",
        this.markerPosition("ENCOUNTER", encounter.name, index),
      );
    });

    travel.forEach((location, index) => {
      this.addMarker(
        location,
        "TRAVEL",
        this.markerPosition("TRAVEL", location.name, index),
      );
    });
  }

  private markerPosition(
    type: MarkerType,
    name: string,
    index: number,
  ): MarkerPosition {
    const key = this.currentProfile.key;
    const lowerName = name.toLowerCase();

    if (key === "blacksmith") return { x: 430, y: 390 };
    if (key === "inn") return { x: 820, y: 430 };
    if (type === "NPC" && lowerName.includes("hagar"))
      return { x: 450, y: 345 };
    if (type === "NPC" && lowerName.includes("elena"))
      return { x: 780, y: 720 };
    if (type === "NPC" && lowerName.includes("kael"))
      return { x: 1010, y: 520 };
    if (type === "NPC" && lowerName.includes("silas"))
      return { x: 680, y: 430 };
    if (type === "ENCOUNTER")
      return { x: key === "city" ? 1270 : 1275, y: 560 };
    if (type === "TRAVEL" && lowerName.includes("outskirts")) {
      return { x: 820, y: 840 };
    }
    if (type === "TRAVEL" && lowerName.includes("greenwood")) {
      return { x: 1410, y: 530 };
    }
    if (type === "TRAVEL" && lowerName.includes("sylvan")) {
      return { x: 1420, y: 610 };
    }
    if (type === "TRAVEL" && lowerName.includes("valeris")) {
      return { x: 180, y: 520 };
    }

    return { x: 320 + index * 180, y: type === "NPC" ? 430 : 620 };
  }

  private addMarker(data: any, type: MarkerType, position: MarkerPosition) {
    const markerTint =
      type === "NPC" ? 0x86efac : type === "ENCOUNTER" ? 0xf87171 : 0xfef08a;
    const sprite = this.add.sprite(
      position.x,
      position.y,
      "player",
      PLAYER_IDLE_FRAME,
    );
    sprite.setScale(type === "TRAVEL" ? 2 : 2.5);
    sprite.setTint(markerTint);
    sprite.setDepth(position.y + 10);
    (sprite as any).markerData = data;
    (sprite as any).markerType = type;
    this.markers?.add(sprite);

    sprite.setAlpha(type === "TRAVEL" ? 0.75 : 1);
  }

  update() {
    if (!this.player || !this.player.body) return;
    const body = this.player.body as Phaser.Physics.Arcade.Body;

    body.setVelocity(0);
    if (this.registry.get("interactionLocked") === true) {
      this.player.anims.stop();
      this.player.setFrame(PLAYER_IDLE_FRAME);
      this.interactionState = "service_overlay";
      this.updateAuditState(false);
      return;
    }

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
    this.player.setDepth(this.player.y);

    this.checkInteractions();
    this.updateAuditState(moving);
  }

  private updateAuditState(moving: boolean) {
    if (!this.auditEnabled || !this.player) return;
    window.__YGGDRASIL_AUDIT__ = {
      ...(window.__YGGDRASIL_AUDIT__ ?? {}),
      world: {
        playerX: this.player.x,
        playerY: this.player.y,
        moving,
        animation: this.player.anims.currentAnim?.key ?? null,
        location: this.currentProfile.title,
        musicKey: this.currentProfile.musicKey,
        combatBackgroundKey: this.currentProfile.combatBackgroundKey,
        nearbyPrompt: this.nearbyPrompt,
        interactionState: this.interactionState,
        movementSpeed: PLAYER_SPEED,
      },
    };
  }

  private checkInteractions() {
    let closestMarker: any = null;
    let minDistance: number = INTERACTION_RADIUS;

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
      const type = closestMarker.markerType as MarkerType;
      const data = closestMarker.markerData;
      const verb =
        type === "NPC" ? "Talk" : type === "ENCOUNTER" ? "Fight" : "Travel";
      const hint = `E ${verb}: ${data.name}`;
      this.nearbyPrompt = hint;
      this.interactionState = type === "NPC" ? "nearby_npc" : "exploring";
      this.interactionHint.setText(hint).setVisible(true);

      if (Phaser.Input.Keyboard.JustDown(this.wasd.E)) {
        this.handleInteraction(type, data);
      }
    } else {
      this.nearbyPrompt = null;
      this.interactionState = "exploring";
      this.interactionHint.setVisible(false);
    }
  }

  private handleInteraction(type: MarkerType, data: any) {
    this.interactionState = "interacting";
    if (type === "NPC") {
      this.game.events.emit("phaser-interact", data);
    } else if (type === "ENCOUNTER") {
      this.game.events.emit("phaser-encounter", data);
    } else {
      this.game.events.emit("phaser-travel", data);
    }
  }
}
