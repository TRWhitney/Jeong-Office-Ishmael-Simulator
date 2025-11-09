from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence

from jeongsimulator.simulation import Action, Card, JeongSimulation, Suit


@dataclass
class StubRng:
    random_values: Iterable[float] | None = None
    suit_values: Iterable[Suit | int] | None = None

    def __post_init__(self) -> None:
        self._random_iter: Iterator[float] = iter(self.random_values or [])
        self._suit_iter: Iterator[Suit | int] = iter(self.suit_values or [])

    def random(self) -> float:
        return next(self._random_iter, 1.0)

    def choice(self, options: Sequence[Suit]) -> Suit:
        value = next(self._suit_iter, options[0])
        if isinstance(value, int):
            return options[value % len(options)]
        if value in options:
            return value
        return options[0]

    def shuffle(self, items: list[Card]) -> None:  # pragma: no cover - deterministic in tests
        return None


def new_sim(
    *,
    deck: list[Card],
    suit: Suit,
    rng: StubRng | None = None,
    bright_potency: int = 0,
    bright_count: int = 3,
) -> JeongSimulation:
    return JeongSimulation(
        rng=rng or StubRng(),
        deck_template=deck,
        shuffle_deck=False,
        initial_suit=suit,
        bright_potency=bright_potency,
        bright_count=bright_count,
    )


def test_attack_discards_off_color_card() -> None:
    sim = new_sim(deck=[Card.S1, Card.S2], suit=Suit.RED)
    sim.start_turn()

    result = sim.resolve(Action.USE_FIRST)

    assert result.used_card == Card.S1
    assert result.match is True
    assert sim.offer == []
    assert sim.discard == [Card.S1, Card.S2]


def test_attack_keeps_same_color_card() -> None:
    sim = new_sim(deck=[Card.S1, Card.S1], suit=Suit.RED)
    sim.start_turn()

    sim.resolve(Action.USE_FIRST)

    assert sim.offer == [Card.S1]
    assert sim.discard == [Card.S1]


def test_s3_bonus_applies_on_match_and_mismatch() -> None:
    sim_match = new_sim(deck=[Card.S3, Card.S1], suit=Suit.BLUE)
    sim_match.start_turn()
    match_result = sim_match.resolve(Action.USE_FIRST)
    assert match_result.bright_delta == 2
    assert sim_match.bright_potency == 2

    sim_mismatch = new_sim(deck=[Card.S3, Card.S1], suit=Suit.YELLOW)
    sim_mismatch.start_turn()
    mismatch_result = sim_mismatch.resolve(Action.USE_FIRST)
    assert mismatch_result.bright_delta == 1
    assert sim_mismatch.bright_potency == 1

    capped = new_sim(deck=[Card.S3, Card.S1], suit=Suit.BLUE, bright_potency=4)
    capped.start_turn()
    capped.resolve(Action.USE_FIRST)
    assert capped.bright_potency == 5


def test_matching_streak_grants_bonus_potency() -> None:
    sim = new_sim(deck=[Card.S2, Card.S1, Card.S2, Card.S1], suit=Suit.YELLOW)

    sim.start_turn()
    first = sim.resolve(Action.USE_FIRST)
    assert first.bright_delta == 1
    sim.end_turn()

    sim.start_turn()
    second = sim.resolve(Action.USE_FIRST)

    assert second.bright_delta == 2
    assert sim.bright_potency == 3


def test_mismatch_breaks_matching_streak() -> None:
    sim = new_sim(deck=[Card.S2, Card.S1, Card.S1, Card.S2, Card.S2], suit=Suit.YELLOW)

    sim.start_turn()
    sim.resolve(Action.USE_FIRST)
    sim.end_turn()

    sim.start_turn()
    mismatch = sim.resolve(Action.USE_FIRST)
    assert mismatch.match is False
    assert mismatch.bright_delta == 0
    sim.end_turn()

    sim.start_turn()
    reset = sim.resolve(Action.USE_FIRST)
    assert reset.bright_delta == 1


def test_cycle_reset_clears_matching_streak() -> None:
    rng = StubRng(suit_values=[Suit.YELLOW])
    sim = new_sim(
        deck=[Card.S2, Card.S1, Card.S2, Card.S1],
        suit=Suit.YELLOW,
        bright_potency=4,
        rng=rng,
    )

    sim.start_turn()
    finishing = sim.resolve(Action.USE_FIRST)
    assert finishing.bright_delta == 1  # cap reached
    sim.end_turn()

    sim.start_turn()
    post_reset = sim.resolve(Action.USE_FIRST)
    assert post_reset.bright_delta == 1


def test_defend_discards_first_and_shuffles_suit() -> None:
    rng = StubRng(random_values=[0.4], suit_values=[Suit.BLUE])
    sim = new_sim(deck=[Card.S1, Card.S2], suit=Suit.RED, rng=rng)
    sim.start_turn()

    resolution = sim.resolve(Action.DEFEND)
    assert resolution.bright_delta == 1
    assert sim.offer == [Card.S2]

    end_state = sim.end_turn()
    assert end_state.cycle_reset is False
    assert sim.bright_count == 2

    sim.start_turn()
    assert sim.current_suit == Suit.BLUE


def test_defend_forces_different_suit_even_if_rng_repeats() -> None:
    rng = StubRng(random_values=[0.6], suit_values=[Suit.YELLOW, Suit.YELLOW])
    sim = new_sim(deck=[Card.S1, Card.S2], suit=Suit.YELLOW, rng=rng)
    sim.start_turn()

    sim.resolve(Action.DEFEND)
    sim.end_turn()

    sim.start_turn()
    assert sim.current_suit != Suit.YELLOW


def test_ego_discards_first_and_always_matches() -> None:
    sim = new_sim(deck=[Card.S1, Card.S2], suit=Suit.YELLOW)
    sim.start_turn()

    result = sim.resolve(Action.EGO)

    assert result.match is True
    assert result.bright_delta == 2
    assert sim.offer == [Card.S2]


def test_kozan_triggers_and_resets_cycle() -> None:
    rng = StubRng(random_values=[0.01, 0.02, 0.96, 0.03, 0.04], suit_values=[Suit.YELLOW])
    sim = new_sim(deck=[Card.S1, Card.S2], suit=Suit.RED, rng=rng, bright_potency=5)
    sim.start_turn()

    end_state = sim.end_turn()

    assert end_state.kozan is not None
    assert end_state.kozan.hits == 4
    assert end_state.cycle_reset is True
    assert sim.bright_potency == 0
    assert sim.bright_count == 3
    assert sim.current_suit == Suit.YELLOW
