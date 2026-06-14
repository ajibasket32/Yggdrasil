from dataclasses import dataclass
from uuid import UUID


class EquipmentRuleError(ValueError):
    """An equipment mutation violates deterministic slot requirements."""


@dataclass(frozen=True)
class EquipmentCandidate:
    inventory_item_id: UUID
    quantity: int
    required_level: int
    compatible_slots: tuple[str, ...]


class EquipmentEngine:
    """Validate equipment compatibility without persistence or AI."""

    @staticmethod
    def validate_equip(
        candidate: EquipmentCandidate,
        *,
        slot_code: str,
        character_level: int,
    ) -> None:
        if candidate.quantity != 1:
            raise EquipmentRuleError("Equippable items must be unique instances")
        if slot_code not in candidate.compatible_slots:
            raise EquipmentRuleError("Item is not compatible with this slot")
        if character_level < candidate.required_level:
            raise EquipmentRuleError("Character does not meet item level requirement")
