"""Tests for the 12-Pokemon roster and the team-building helpers."""

from __future__ import annotations

import random

import pytest

from climon.assets import load_sprite
from climon.engine.data import (
    ROSTER,
    STARTERS,
    make_team,
    random_team,
    species_by_name,
)


def test_roster_has_twelve_unique_pokemon() -> None:
    assert len(ROSTER) == 12
    assert len({species.name for species in ROSTER}) == 12
    for starter in STARTERS:
        assert starter in ROSTER


def test_every_species_is_well_formed() -> None:
    for species in ROSTER:
        assert species.sprite_key
        assert 1 <= len(species.types) <= 2
        assert len(species.moves) >= 2


def test_every_species_has_front_and_back_sprites() -> None:
    for species in ROSTER:
        for view in ("front", "back"):
            assert load_sprite(species.sprite_key, view).strip()


def test_make_team_keeps_pick_order_with_first_as_lead() -> None:
    team = make_team(["Pikachu", "Gengar", "Snorlax"])
    assert [member.name for member in team.members] == ["Pikachu", "Gengar", "Snorlax"]
    assert team.active_index == 0


def test_random_team_is_distinct_and_correctly_sized() -> None:
    team = random_team(random.Random(1), size=3)
    assert len(team.members) == 3
    assert len({member.name for member in team.members}) == 3


def test_species_by_name_is_case_insensitive_and_rejects_unknown() -> None:
    assert species_by_name("mEwTwO").name == "Mewtwo"
    with pytest.raises(KeyError):
        species_by_name("Missingno")
