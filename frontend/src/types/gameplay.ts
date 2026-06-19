export interface Race {
  id: string;
  name: string;
  description: string;
  category: string;
}

export interface Job {
  id: string;
  name: string;
  description: string;
  tier: string;
}

export interface Location {
  id: string;
  name: string;
  location_type: string;
  description: string;
  danger_level: number;
  discovered: boolean;
  reachable: boolean;
}

export interface CharacterDefinitions {
  races: Race[];
  starting_jobs: Job[];
  starting_location: Location;
}

export interface StatBlock {
  strength: number;
  dexterity: number;
  agility: number;
  vitality: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
}

export interface DerivedStatBlock {
  max_hp: number;
  max_mp: number;
  max_stamina: number;
  physical_attack: number;
  physical_defense: number;
  magic_attack: number;
  magic_defense: number;
  accuracy: number;
  evasion: number;
  critical_chance: number;
  initiative: number;
}

export interface Skill {
  id: string;
  name: string;
  description: string;
  skill_type: string;
  skill_level: number;
  mana_cost: number;
  cooldown: number;
  target_type: string;
  effect_definitions: { effect: string; magnitude: number }[];
}

export interface JobProgress {
  job: Job;
  job_level: number;
  experience: number;
  experience_to_next: number;
  active: boolean;
}

export interface CharacterSummary {
  id: string;
  name: string;
  race: Race;
  level: number;
  current_job: Job;
  current_location: Location;
}

export interface CharacterSheet extends CharacterSummary {
  gender: string;
  alignment: string;
  experience: number;
  experience_to_next: number;
  skill_points: number;
  stats: StatBlock;
  derived_stats: DerivedStatBlock;
  current_hp: number;
  current_mp: number;
  current_stamina: number;
  gold: number;
  fame: number;
  karma: number;
  jobs: JobProgress[];
  skills: Skill[];
}

export interface Inventory {
  slot_count: number;
  used_slots: number;
  total_weight: number;
  max_weight: number;
  items: {
    inventory_item_id: string;
    name: string;
    item_type: string;
    rarity: string;
    quantity: number;
    is_quest_item: boolean;
    is_equipped: boolean;
  }[];
}

export interface Equipment {
  slots: {
    slot_id: string;
    code: string;
    name: string;
    item: { name: string } | null;
  }[];
  total_equipment_bonuses: Record<string, number>;
}

export interface CreateCharacterInput {
  name: string;
  race_id: string;
  gender: string;
  alignment: "GOOD" | "NEUTRAL" | "EVIL";
  starting_job_id: string;
}

export interface EncounterDefinition {
  id: string;
  name: string;
  monster_name: string;
  monster_level: number;
  difficulty: string;
  location_id: string;
  reward_experience: number;
  reward_gold: number;
}

export type CombatStatus = "ACTIVE" | "VICTORY" | "DEFEAT" | "FLED";
export type CombatActionType = "ATTACK" | "SKILL" | "ITEM" | "GUARD" | "WAIT";

export interface CombatParticipant {
  id: string;
  source_id: string;
  name: string;
  side: "PLAYER" | "ENEMY";
  level: number;
  current_hp: number;
  max_hp: number;
  current_mp: number;
  max_mp: number;
  current_stamina: number;
  max_stamina: number;
  guarding: boolean;
  defeated: boolean;
  statuses: { code: string; duration: number; potency: number }[];
}

export interface CombatLogEntry {
  id: string;
  sequence: number;
  round_number: number;
  action_type: string;
  outcome: Record<string, unknown>;
  text: string;
  created_at: string;
}

export interface CombatState {
  combat_id: string;
  encounter_name: string;
  seed: number;
  status: CombatStatus;
  round_number: number;
  action_sequence: number;
  turn_order: string[];
  participants: CombatParticipant[];
  rewards: {
    experience: number;
    gold: number;
    items: string[];
  };
  recent_log: CombatLogEntry[];
}

export type QuestStatus =
  | "NOT_STARTED"
  | "ACTIVE"
  | "COMPLETED"
  | "FAILED"
  | "ARCHIVED";

export interface Quest {
  id: string;
  title: string;
  description: string;
  minimum_level: number;
  status: QuestStatus;
  objectives_complete: boolean;
  rewards_claimed: boolean;
  current_step: number;
  steps: {
    id: string;
    sequence: number;
    objective_type: string;
    target_id: string;
    description: string;
    required_count: number;
    progress: number;
    complete: boolean;
  }[];
  rewards: { experience: number; gold: number; reputation: number };
}

export interface Npc {
  id: string;
  name: string;
  occupation: string;
  role: string;
  faction_id: string | null;
  current_location_id: string;
  personality_profile: Record<string, unknown>;
  knowledge: Record<string, unknown>;
  is_alive: boolean;
  available_actions: ("GREET" | "OFFER_HELP")[];
  shop_id?: string;
}

export interface ShopItem {
  item_id: string;
  name: string;
  description: string;
  price: number;
  rarity: string;
  item_type: string;
}

export interface Shop {
  id: string;
  name: string;
  description: string;
  owner_npc_id: string;
  items: ShopItem[];
}

export interface ShopPurchaseResult {
  character_id: string;
  item_id: string;
  price_paid: number;
  gold_remaining: number;
}

export interface InnRestResult {
  character_id: string;
  hp_restored: number;
  mp_restored: number;
  price_paid: number;
  gold_remaining: number;
  current_hp: number;
  current_mp: number;
}

export interface Relationship {
  npc_id: string;
  character_id: string;
  trust: number;
  friendship: number;
  respect: number;
  fear: number;
  hatred: number;
  loyalty: number;
}

export interface NpcInteraction {
  npc: Npc;
  relationship: Relationship;
  action_id: string;
  result_text: string;
  quest_progressed: boolean;
}

export interface Faction {
  id: string;
  name: string;
  description: string;
  reputation: number;
  rank: string;
  joined: boolean;
}

export interface Dungeon {
  id: string;
  name: string;
  description: string;
  location_id: string;
  recommended_level: number;
  entered: boolean;
  cleared: boolean;
  boss_alive: boolean;
}

export interface JournalEntry {
  id: string;
  category: string;
  title: string;
  body: string;
  quest_id: string | null;
  created_at: string;
}

export type DialogueTopic = "GREETING" | "QUEST" | "LOCAL_NEWS" | "FAREWELL";

export interface Narrative {
  speaker_name: string | null;
  text: string;
  tone: string;
  tags: string[];
  fallback_used: boolean;
  cached: boolean;
  prompt_version: string;
  context_memory_count: number;
  available_topics: DialogueTopic[];
}
