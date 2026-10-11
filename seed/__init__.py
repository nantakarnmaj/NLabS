"""Seed package export."""

from seed.rooms import seed_rooms
from seed.suction_mission_seed import seed_suction_mission
from seed.oxygen_mission_seed import seed_oxygen_mission
from seed.nebulization_mission_seed import seed_nebulization_mission
from seed.rescue_mission_seed import seed_rescue_mission


def run_all_seeds() -> dict[str, int]:
    """Execute all seed routines idempotently."""
    room_results = seed_rooms()
    suction_results = seed_suction_mission()
    oxygen_results = seed_oxygen_mission()
    nebulization_results = seed_nebulization_mission()
    rescue_results = seed_rescue_mission()
    return {
        "missions": room_results.get("created_missions", 0),
        "prerequisites": room_results.get("created_prereqs", 0),
        "activities": (
            suction_results.get("activities", 0)
            + oxygen_results.get("activities", 0)
            + nebulization_results.get("activities", 0)
            + rescue_results.get("activities", 0)
        ),
    }


__all__ = [
    "seed_rooms",
    "seed_suction_mission",
    "seed_oxygen_mission",
    "seed_nebulization_mission",
    "seed_rescue_mission",
    "run_all_seeds",
]
