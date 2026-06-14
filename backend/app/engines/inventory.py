from dataclasses import dataclass
from uuid import UUID, uuid4


class InventoryRuleError(ValueError):
    """An inventory mutation violates deterministic item rules."""


@dataclass(frozen=True)
class ItemRule:
    item_id: UUID
    weight: float
    is_stackable: bool
    max_stack: int
    is_quest_item: bool
    is_droppable: bool


@dataclass(frozen=True)
class InventoryEntry:
    entry_id: UUID
    item_id: UUID
    quantity: int
    slot_index: int
    unique_instance_id: UUID | None


@dataclass(frozen=True)
class PlannedEntry:
    item_id: UUID
    quantity: int
    slot_index: int
    unique_instance_id: UUID | None


class InventoryEngine:
    """Plan stack, unique-item, drop, split, merge, and sort mutations."""

    @staticmethod
    def total_weight(
        entries: list[InventoryEntry],
        rules: dict[UUID, ItemRule],
    ) -> float:
        return round(
            sum(rules[entry.item_id].weight * entry.quantity for entry in entries),
            2,
        )

    @classmethod
    def plan_add(
        cls,
        entries: list[InventoryEntry],
        rule: ItemRule,
        quantity: int,
        *,
        slot_count: int,
        current_weight: float,
        max_weight: float,
    ) -> tuple[list[tuple[UUID, int]], list[PlannedEntry]]:
        if quantity <= 0:
            raise InventoryRuleError("Quantity must be positive")
        if current_weight + rule.weight * quantity > max_weight:
            raise InventoryRuleError("Inventory weight limit exceeded")

        updates: list[tuple[UUID, int]] = []
        creates: list[PlannedEntry] = []
        remaining = quantity
        occupied = {entry.slot_index for entry in entries}

        if rule.is_stackable:
            for entry in sorted(entries, key=lambda value: value.slot_index):
                if entry.item_id != rule.item_id or entry.quantity >= rule.max_stack:
                    continue
                moved = min(rule.max_stack - entry.quantity, remaining)
                updates.append((entry.entry_id, entry.quantity + moved))
                remaining -= moved
                if remaining == 0:
                    return updates, creates

        free_slots = [index for index in range(slot_count) if index not in occupied]
        while remaining > 0:
            if not free_slots:
                raise InventoryRuleError("Inventory has no free slots")
            moved = min(rule.max_stack, remaining) if rule.is_stackable else 1
            creates.append(
                PlannedEntry(
                    item_id=rule.item_id,
                    quantity=moved,
                    slot_index=free_slots.pop(0),
                    unique_instance_id=None if rule.is_stackable else uuid4(),
                )
            )
            remaining -= moved
        return updates, creates

    @staticmethod
    def validate_drop(entry: InventoryEntry, rule: ItemRule, quantity: int) -> None:
        if quantity <= 0 or quantity > entry.quantity:
            raise InventoryRuleError("Invalid drop quantity")
        if rule.is_quest_item or not rule.is_droppable:
            raise InventoryRuleError("Quest or protected items cannot be dropped")

    @staticmethod
    def split(
        entry: InventoryEntry,
        rule: ItemRule,
        quantity: int,
        free_slot: int | None,
    ) -> PlannedEntry:
        if not rule.is_stackable:
            raise InventoryRuleError("Unique items cannot be split")
        if quantity <= 0 or quantity >= entry.quantity:
            raise InventoryRuleError("Split quantity must leave both stacks non-empty")
        if free_slot is None:
            raise InventoryRuleError("Inventory has no free slots")
        return PlannedEntry(rule.item_id, quantity, free_slot, None)

    @staticmethod
    def merge(
        source: InventoryEntry,
        target: InventoryEntry,
        rule: ItemRule,
    ) -> tuple[int, int]:
        if source.entry_id == target.entry_id or source.item_id != target.item_id:
            raise InventoryRuleError("Only distinct matching stacks can merge")
        if not rule.is_stackable:
            raise InventoryRuleError("Unique items cannot merge")
        moved = min(rule.max_stack - target.quantity, source.quantity)
        if moved <= 0:
            raise InventoryRuleError("Target stack is full")
        return source.quantity - moved, target.quantity + moved

    @staticmethod
    def sorted_slots(
        entries: list[InventoryEntry],
        item_names: dict[UUID, str],
    ) -> dict[UUID, int]:
        ordered = sorted(
            entries,
            key=lambda entry: (
                item_names[entry.item_id].casefold(),
                str(entry.unique_instance_id or ""),
                str(entry.entry_id),
            ),
        )
        return {entry.entry_id: index for index, entry in enumerate(ordered)}
