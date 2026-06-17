from dataclasses import dataclass
from uuid import UUID


class NavigationRuleError(ValueError):
    """A requested travel edge is invalid."""


@dataclass(frozen=True)
class TravelRoute:
    origin_id: UUID
    destination_id: UUID
    requirements: dict[str, object]


class NavigationEngine:
    """Validate movement against the canonical directed location graph."""

    @staticmethod
    def validate_travel(
        current_location_id: UUID,
        destination_id: UUID,
        routes: list[TravelRoute],
        *,
        character_level: int,
    ) -> TravelRoute:
        route = next(
            (
                candidate
                for candidate in routes
                if candidate.origin_id == current_location_id
                and candidate.destination_id == destination_id
            ),
            None,
        )
        if route is None:
            raise NavigationRuleError("No direct route connects these locations")
        raw_minimum = route.requirements.get("minimum_level", 1)
        if isinstance(raw_minimum, bool) or not isinstance(raw_minimum, int | str):
            raise NavigationRuleError("Route level requirement must be an integer")
        try:
            minimum_level = int(raw_minimum)
        except ValueError as error:
            raise NavigationRuleError(
                "Route level requirement must be an integer"
            ) from error
        if character_level < minimum_level:
            raise NavigationRuleError("Character does not meet route requirements")
        return route
