import type { EncounterDefinition, Location, Npc } from "../types/gameplay";

export type MarkerType = "NPC" | "ENCOUNTER" | "TRAVEL";

export type WorldMusicKey =
  | "title_theme"
  | "valeris_city"
  | "valeris_outskirts"
  | "sylvan_branch"
  | "battle_theme";

export interface MapRect {
  x: number;
  y: number;
  width: number;
  height: number;
  color: number;
  alpha?: number;
  label?: string;
  collides?: boolean;
}

export interface MapCircle {
  x: number;
  y: number;
  radius: number;
  color: number;
  alpha?: number;
  label?: string;
  collides?: boolean;
}

export interface MapMarkerSlot {
  key: string;
  x: number;
  y: number;
}

export interface WorldMapDefinition {
  mapId: string;
  locationNames: string[];
  regionType: string;
  theme: string;
  musicKey: WorldMusicKey;
  combatBackgroundKey: string;
  width: number;
  height: number;
  backgroundColor: number;
  spawn: { x: number; y: number };
  roads: MapRect[];
  terrain: MapRect[];
  props: MapRect[];
  circles: MapCircle[];
  npcSlots: MapMarkerSlot[];
  encounterSlots: MapMarkerSlot[];
  travelSlots: MapMarkerSlot[];
  landmarks: string[];
}

const CITY_STONE = 0x8d99ae;
const CITY_ROOF = 0x5f3434;
const GRASS = 0x4f8a52;
const DARK_GRASS = 0x2f5f3b;
const DIRT = 0x9b7653;
const WOOD = 0x7a5230;
const WATER = 0x3b82a0;
const TREE = 0x1f6f43;
const TREE_DARK = 0x164a31;
const ROCK = 0x6b7280;
const LIGHT = 0xeab308;

export const WORLD_MAPS: WorldMapDefinition[] = [
  {
    mapId: "valeris_outskirts",
    locationNames: ["Valeris Outskirts"],
    regionType: "route",
    theme: "countryside_gate",
    musicKey: "valeris_outskirts",
    combatBackgroundKey: "roadside_field",
    width: 1280,
    height: 900,
    backgroundColor: GRASS,
    spawn: { x: 300, y: 470 },
    roads: [
      { x: 640, y: 470, width: 1180, height: 170, color: DIRT },
      { x: 240, y: 470, width: 260, height: 260, color: CITY_STONE },
      { x: 790, y: 575, width: 460, height: 80, color: DIRT },
    ],
    terrain: [
      { x: 250, y: 190, width: 500, height: 200, color: DARK_GRASS },
      { x: 1000, y: 245, width: 360, height: 260, color: DARK_GRASS },
      { x: 850, y: 760, width: 520, height: 120, color: DARK_GRASS },
    ],
    props: [
      {
        x: 120,
        y: 470,
        width: 60,
        height: 320,
        color: CITY_ROOF,
        collides: true,
        label: "Gate",
      },
      { x: 360, y: 350, width: 260, height: 24, color: WOOD, collides: true },
      { x: 640, y: 350, width: 260, height: 24, color: WOOD, collides: true },
      { x: 620, y: 650, width: 260, height: 24, color: WOOD, collides: true },
      { x: 940, y: 650, width: 260, height: 24, color: WOOD, collides: true },
      { x: 1010, y: 470, width: 90, height: 48, color: ROCK, collides: true },
    ],
    circles: [
      { x: 460, y: 190, radius: 54, color: TREE, collides: true },
      { x: 610, y: 205, radius: 48, color: TREE, collides: true },
      { x: 1080, y: 250, radius: 62, color: TREE_DARK, collides: true },
      { x: 930, y: 270, radius: 42, color: TREE, collides: true },
      { x: 1030, y: 770, radius: 58, color: TREE_DARK, collides: true },
    ],
    npcSlots: [{ key: "default", x: 425, y: 500 }],
    encounterSlots: [{ key: "default", x: 900, y: 570 }],
    travelSlots: [
      { key: "Valeris City", x: 175, y: 470 },
      { key: "Greenwood Verge", x: 1110, y: 470 },
      { key: "Stonewatch Mine", x: 720, y: 705 },
    ],
    landmarks: ["city gate", "fenced road", "forest edge"],
  },
  {
    mapId: "valeris_city",
    locationNames: ["Valeris City"],
    regionType: "safe_hub",
    theme: "capital_market",
    musicKey: "valeris_city",
    combatBackgroundKey: "city_training_ring",
    width: 1200,
    height: 900,
    backgroundColor: 0x566072,
    spawn: { x: 610, y: 720 },
    roads: [
      { x: 600, y: 700, width: 260, height: 330, color: CITY_STONE },
      { x: 600, y: 470, width: 820, height: 220, color: CITY_STONE },
      { x: 600, y: 470, width: 250, height: 760, color: 0xa7b0c0, alpha: 0.65 },
    ],
    terrain: [
      {
        x: 600,
        y: 470,
        width: 260,
        height: 160,
        color: 0xc7d2fe,
        alpha: 0.25,
        label: "Plaza",
      },
      { x: 220, y: 610, width: 220, height: 160, color: 0x3f6212, alpha: 0.8 },
      { x: 980, y: 610, width: 220, height: 160, color: 0x3f6212, alpha: 0.8 },
    ],
    props: [
      {
        x: 275,
        y: 315,
        width: 260,
        height: 190,
        color: 0x7f1d1d,
        collides: true,
        label: "Forge",
      },
      {
        x: 270,
        y: 420,
        width: 170,
        height: 38,
        color: 0xf97316,
        collides: true,
      },
      {
        x: 900,
        y: 320,
        width: 250,
        height: 180,
        color: 0x854d0e,
        collides: true,
        label: "Inn",
      },
      { x: 905, y: 430, width: 160, height: 36, color: WOOD, collides: true },
      {
        x: 600,
        y: 170,
        width: 420,
        height: 95,
        color: 0x374151,
        collides: true,
        label: "North Gate",
      },
      {
        x: 455,
        y: 470,
        width: 38,
        height: 180,
        color: LIGHT,
        alpha: 0.9,
        collides: true,
      },
      {
        x: 745,
        y: 470,
        width: 38,
        height: 180,
        color: LIGHT,
        alpha: 0.9,
        collides: true,
      },
    ],
    circles: [
      { x: 190, y: 625, radius: 48, color: TREE, collides: true },
      { x: 1020, y: 625, radius: 48, color: TREE, collides: true },
    ],
    npcSlots: [
      { key: "Blacksmith Hagar", x: 320, y: 485 },
      { key: "Merchant Silas", x: 610, y: 455 },
      { key: "default", x: 610, y: 455 },
    ],
    encounterSlots: [{ key: "default", x: 720, y: 565 }],
    travelSlots: [{ key: "Valeris Outskirts", x: 610, y: 805 }],
    landmarks: ["forge", "inn", "market plaza", "north gate"],
  },
  {
    mapId: "greenwood_verge",
    locationNames: ["Greenwood Verge", "Valerian Forest"],
    regionType: "forest_route",
    theme: "woodland_threshold",
    musicKey: "sylvan_branch",
    combatBackgroundKey: "forest_path",
    width: 1280,
    height: 920,
    backgroundColor: DARK_GRASS,
    spawn: { x: 210, y: 570 },
    roads: [
      { x: 560, y: 585, width: 920, height: 130, color: DIRT },
      { x: 915, y: 430, width: 240, height: 90, color: DIRT },
      { x: 390, y: 720, width: 360, height: 90, color: DIRT },
    ],
    terrain: [
      { x: 360, y: 310, width: 480, height: 180, color: GRASS },
      { x: 870, y: 760, width: 510, height: 120, color: GRASS },
      {
        x: 350,
        y: 740,
        width: 210,
        height: 140,
        color: 0x854d0e,
        alpha: 0.8,
        label: "Road Inn",
      },
    ],
    props: [
      {
        x: 360,
        y: 745,
        width: 190,
        height: 120,
        color: 0x92400e,
        collides: true,
        label: "Inn",
      },
      { x: 580, y: 590, width: 120, height: 22, color: WOOD, collides: true },
      { x: 780, y: 590, width: 120, height: 22, color: WOOD, collides: true },
      { x: 1045, y: 430, width: 120, height: 36, color: ROCK, collides: true },
    ],
    circles: [
      { x: 230, y: 250, radius: 68, color: TREE, collides: true },
      { x: 380, y: 235, radius: 64, color: TREE_DARK, collides: true },
      { x: 560, y: 285, radius: 62, color: TREE, collides: true },
      { x: 1000, y: 230, radius: 80, color: TREE_DARK, collides: true },
      { x: 1115, y: 730, radius: 70, color: TREE, collides: true },
    ],
    npcSlots: [
      { key: "Scout Kael", x: 705, y: 455 },
      { key: "Innkeeper Elena", x: 375, y: 650 },
      { key: "default", x: 530, y: 530 },
    ],
    encounterSlots: [{ key: "default", x: 860, y: 660 }],
    travelSlots: [
      { key: "Valeris Outskirts", x: 145, y: 590 },
      { key: "Sylvan Branch", x: 1085, y: 400 },
      { key: "Ancient Crossroads", x: 920, y: 775 },
    ],
    landmarks: ["road inn", "scout trail", "forest canopy"],
  },
  {
    mapId: "sylvan_branch",
    locationNames: ["Sylvan Branch"],
    regionType: "quest_area",
    theme: "deep_forest_creek",
    musicKey: "sylvan_branch",
    combatBackgroundKey: "forest_creek",
    width: 1320,
    height: 960,
    backgroundColor: TREE_DARK,
    spawn: { x: 180, y: 760 },
    roads: [
      { x: 360, y: 755, width: 430, height: 110, color: DIRT },
      { x: 620, y: 570, width: 150, height: 430, color: DIRT },
      { x: 845, y: 390, width: 420, height: 120, color: DIRT },
      { x: 680, y: 520, width: 170, height: 60, color: WOOD, label: "Bridge" },
    ],
    terrain: [
      { x: 700, y: 500, width: 120, height: 820, color: WATER, alpha: 0.8 },
      {
        x: 965,
        y: 385,
        width: 360,
        height: 170,
        color: GRASS,
        alpha: 0.7,
        label: "Clearing",
      },
      { x: 425, y: 215, width: 330, height: 140, color: GRASS, alpha: 0.55 },
    ],
    props: [
      { x: 690, y: 520, width: 190, height: 24, color: WOOD, collides: false },
      { x: 525, y: 595, width: 46, height: 190, color: TREE, collides: true },
      { x: 860, y: 560, width: 42, height: 210, color: TREE, collides: true },
      { x: 995, y: 405, width: 80, height: 36, color: ROCK, collides: true },
    ],
    circles: [
      { x: 210, y: 230, radius: 92, color: TREE, collides: true },
      { x: 420, y: 185, radius: 84, color: TREE_DARK, collides: true },
      { x: 1060, y: 180, radius: 96, color: TREE, collides: true },
      { x: 1160, y: 685, radius: 88, color: TREE_DARK, collides: true },
      { x: 300, y: 890, radius: 76, color: TREE, collides: true },
    ],
    npcSlots: [{ key: "default", x: 540, y: 680 }],
    encounterSlots: [
      { key: "Buzzing Shadows", x: 970, y: 390 },
      { key: "Guardian of the Path", x: 1045, y: 500 },
      { key: "default", x: 970, y: 390 },
    ],
    travelSlots: [{ key: "Greenwood Verge", x: 150, y: 780 }],
    landmarks: ["creek", "bridge", "monster clearing", "dense canopy"],
  },
];

const FALLBACK_MAP: WorldMapDefinition = {
  mapId: "generic_valeria",
  locationNames: [],
  regionType: "route",
  theme: "valerian_field",
  musicKey: "valeris_outskirts",
  combatBackgroundKey: "field",
  width: 1000,
  height: 760,
  backgroundColor: GRASS,
  spawn: { x: 500, y: 380 },
  roads: [{ x: 500, y: 380, width: 860, height: 130, color: DIRT }],
  terrain: [{ x: 500, y: 180, width: 700, height: 180, color: DARK_GRASS }],
  props: [
    {
      x: 500,
      y: 120,
      width: 240,
      height: 45,
      color: ROCK,
      collides: true,
      label: "Landmark",
    },
  ],
  circles: [
    { x: 260, y: 230, radius: 56, color: TREE, collides: true },
    { x: 780, y: 545, radius: 56, color: TREE_DARK, collides: true },
  ],
  npcSlots: [{ key: "default", x: 360, y: 370 }],
  encounterSlots: [{ key: "default", x: 650, y: 370 }],
  travelSlots: [{ key: "default", x: 840, y: 380 }],
  landmarks: ["road", "field", "landmark"],
};

export const mapForLocation = (locationName?: string): WorldMapDefinition => {
  if (!locationName) return FALLBACK_MAP;
  return (
    WORLD_MAPS.find((map) => map.locationNames.includes(locationName)) ??
    FALLBACK_MAP
  );
};

export const musicKeyForLocation = (locationName?: string): WorldMusicKey =>
  mapForLocation(locationName).musicKey;

const findSlot = (
  slots: MapMarkerSlot[],
  preferredKey: string | undefined,
  index: number,
): MapMarkerSlot => {
  const named = preferredKey
    ? slots.find((slot) => preferredKey.includes(slot.key))
    : undefined;
  return (
    named ?? slots[index] ?? slots[0] ?? { key: "default", x: 500, y: 380 }
  );
};

export const markerPosition = (
  map: WorldMapDefinition,
  type: MarkerType,
  data: Npc | EncounterDefinition | Location,
  index: number,
): { x: number; y: number } => {
  const name = "name" in data ? data.name : undefined;
  const slots =
    type === "NPC"
      ? map.npcSlots
      : type === "ENCOUNTER"
        ? map.encounterSlots
        : map.travelSlots;
  const slot = findSlot(slots, name, index);
  return { x: slot.x, y: slot.y };
};
