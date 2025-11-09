"""Core logic for the Jeong Office Ishmael simulator."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, List


class Suit(str, Enum):
    RED = "Red"
    YELLOW = "Yellow"
    BLUE = "Blue"


class Card(str, Enum):
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"


CARD_COLORS: dict[Card, Suit] = {
    Card.S1: Suit.RED,
    Card.S2: Suit.YELLOW,
    Card.S3: Suit.BLUE,
}

DEFAULT_DECK: list[Card] = [
    Card.S1,
    Card.S1,
    Card.S1,
    Card.S2,
    Card.S2,
    Card.S3,
]


class Action(str, Enum):
    USE_FIRST = "use_first"
    USE_SECOND = "use_second"
    DEFEND = "defend"
    EGO = "ego"


@dataclass(frozen=True)
class TurnSnapshot:
    suit: Suit
    bright_potency: int
    bright_count: int
    offer: tuple[Card, ...]
    available_actions: tuple[Action, ...]


@dataclass(frozen=True)
class KozanResult:
    flips: tuple[str, ...]
    hits: int
    potency_before: int


@dataclass(frozen=True)
class ActionResolution:
    action: Action
    used_card: Card | None
    match: bool | None
    bright_delta: int
    bright_potency: int
    bright_count: int
    offer: tuple[Card, ...]
    messages: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TurnEndResult:
    bright_potency: int
    bright_count: int
    cycle_reset: bool
    suit_shuffle_pending: bool
    kozan: KozanResult | None = None
    new_suit: Suit | None = None


class JeongSimulation:
    """Stateful simulation following the Jeong Ishmael spec."""

    def __init__(
        self,
        *,
        rng: random.Random | None = None,
        deck_template: Iterable[Card] | None = None,
        shuffle_deck: bool = True,
        initial_suit: Suit | None = None,
        bright_potency: int = 0,
        bright_count: int = 3,
    ) -> None:
        self.rng = rng or random.Random()
        self.deck_template: list[Card] = list(deck_template or DEFAULT_DECK)
        self.shuffle_deck = shuffle_deck
        self.current_suit: Suit = initial_suit or self._random_suit()
        self.bright_potency = bright_potency
        self.bright_count = bright_count
        self.deck: list[Card] = []
        self.discard: list[Card] = []
        self.offer: list[Card] = []
        self.pending_suit_shuffle = False
        self._next_suit: Suit | None = None
        self.turn_started = False
        self.previous_turn_matched = False
        self._reset_to_template()

    def _random_suit(self, exclude: Suit | None = None) -> Suit:
        options = [s for s in Suit if s != exclude] if exclude else list(Suit)
        return self.rng.choice(options)

    def _reset_to_template(self) -> None:
        self.deck = list(self.deck_template)
        if self.shuffle_deck:
            self.rng.shuffle(self.deck)
        self.discard = []

    def _recycle_deck(self) -> None:
        if self.discard:
            fresh_cards = list(self.discard)
            self.discard = []
        else:
            fresh_cards = list(self.deck_template)
        if self.shuffle_deck:
            self.rng.shuffle(fresh_cards)
        self.deck = fresh_cards

    def start_turn(self) -> TurnSnapshot:
        if self.turn_started:
            raise RuntimeError("Turn already started; call end_turn() first")
        if self.pending_suit_shuffle:
            self.current_suit = self._next_suit or self._random_suit(exclude=self.current_suit)
            self.pending_suit_shuffle = False
            self._next_suit = None
        self._refill_offer()
        self.turn_started = True
        return self._snapshot()

    def _snapshot(self) -> TurnSnapshot:
        actions = [Action.USE_FIRST]
        if len(self.offer) >= 2:
            actions.append(Action.USE_SECOND)
        actions.extend([Action.DEFEND, Action.EGO])
        return TurnSnapshot(
            suit=self.current_suit,
            bright_potency=self.bright_potency,
            bright_count=self.bright_count,
            offer=tuple(self.offer),
            available_actions=tuple(actions),
        )

    def resolve(self, action: Action) -> ActionResolution:
        if not self.turn_started:
            raise RuntimeError("Call start_turn() before resolving an action")
        if action is Action.USE_FIRST:
            return self._use_attack(0)
        if action is Action.USE_SECOND:
            return self._use_attack(1)
        if action is Action.DEFEND:
            return self._defend()
        if action is Action.EGO:
            return self._ego()
        raise ValueError(f"Unsupported action: {action}")

    def _refill_offer(self) -> None:
        while len(self.offer) < 2:
            self.offer.append(self._draw_card())

    def _draw_card(self) -> Card:
        if not self.deck:
            self._recycle_deck()
        return self.deck.pop(0)

    def _use_attack(self, index: int) -> ActionResolution:
        if index >= len(self.offer):
            raise ValueError("Selected attack is not available")
        card = self.offer.pop(index)
        used_color = CARD_COLORS[card]
        match = used_color == self.current_suit
        bright_delta = 0
        messages: List[str] = [f"Used {card.value} ({used_color.value})"]
        if match:
            bright_delta += 1
            messages.append("Match +1 Bright")
        else:
            messages.append("Mismatch +0 Bright")
        if match and self.previous_turn_matched:
            bright_delta += 1
            messages.append("Streak bonus +1 Bright")
        if card is Card.S3:
            bright_delta += 1
            messages.append("S3 bonus +1 Bright")
        bright_delta = self._increment_bright(bright_delta)
        self.discard.append(card)

        if len(self.offer) == 1:
            remaining = CARD_COLORS[self.offer[0]]
            if remaining != used_color:
                discarded = self.offer.pop(0)
                self.discard.append(discarded)
                messages.append("Discarded off-color follow-up")
            else:
                messages.append("Kept matching follow-up")

        messages.append(self._bright_status())
        self.previous_turn_matched = match
        return ActionResolution(
            action=Action.USE_FIRST if index == 0 else Action.USE_SECOND,
            used_card=card,
            match=match,
            bright_delta=bright_delta,
            bright_potency=self.bright_potency,
            bright_count=self.bright_count,
            offer=tuple(self.offer),
            messages=tuple(messages),
        )

    def _defend(self) -> ActionResolution:
        discarded = self._discard_first_offer()
        gained = 1 if self.rng.random() < 0.5 else 0
        bright_delta = self._increment_bright(gained)
        self.pending_suit_shuffle = True
        self._next_suit = self._random_suit(exclude=self.current_suit)
        self.previous_turn_matched = False
        messages = ["Defend (Counter)"]
        if discarded:
            messages.append(f"Discarded {discarded.value}")
        messages.append(
            "Bright +1" if bright_delta else "Bright +0"
        )
        if self.pending_suit_shuffle:
            messages.append("Suit will shuffle next turn")
        messages.append(self._bright_status())
        return ActionResolution(
            action=Action.DEFEND,
            used_card=None,
            match=None,
            bright_delta=bright_delta,
            bright_potency=self.bright_potency,
            bright_count=self.bright_count,
            offer=tuple(self.offer),
            messages=tuple(messages),
        )

    def _ego(self) -> ActionResolution:
        self._discard_first_offer()
        requested = 2
        messages = ["EGO unleashed", "Always matches"]
        if self.previous_turn_matched:
            requested += 1
            messages.append("Streak bonus +1 Bright")
        bright_delta = self._increment_bright(requested)
        self.previous_turn_matched = True
        messages.append(self._bright_status())
        return ActionResolution(
            action=Action.EGO,
            used_card=None,
            match=True,
            bright_delta=bright_delta,
            bright_potency=self.bright_potency,
            bright_count=self.bright_count,
            offer=tuple(self.offer),
            messages=tuple(messages),
        )

    def _discard_first_offer(self) -> Card | None:
        if not self.offer:
            return None
        card = self.offer.pop(0)
        self.discard.append(card)
        return card

    def _increment_bright(self, delta: int) -> int:
        if delta <= 0:
            return 0
        before = self.bright_potency
        self.bright_potency = min(5, self.bright_potency + delta)
        return self.bright_potency - before

    def _bright_status(self) -> str:
        return f"Bright {self.bright_potency}/5 | Count {self.bright_count}"

    def end_turn(self) -> TurnEndResult:
        if not self.turn_started:
            raise RuntimeError("Cannot end a turn that never started")
        self.turn_started = False
        self.bright_count = max(0, self.bright_count - 1)
        cycle_reset = False
        kozan: KozanResult | None = None
        if self.bright_potency == 5 or self.bright_count == 0:
            cycle_reset = True
            potency_before = self.bright_potency
            if potency_before >= 3:
                kozan = self._run_kozan(potency_before)
            self.bright_potency = 0
            self.bright_count = 3
            self.current_suit = self._random_suit()
            self.pending_suit_shuffle = False
            self._next_suit = None
            self.previous_turn_matched = False
        return TurnEndResult(
            bright_potency=self.bright_potency,
            bright_count=self.bright_count,
            cycle_reset=cycle_reset,
            suit_shuffle_pending=self.pending_suit_shuffle,
            kozan=kozan,
            new_suit=self.current_suit if cycle_reset else None,
        )

    def _run_kozan(self, potency_before: int) -> KozanResult:
        flips: List[str] = []
        hits = 0
        for _ in range(min(potency_before, 5)):
            if self.rng.random() < 0.95:
                flips.append("H")
                hits += 1
            else:
                flips.append("T")
        return KozanResult(flips=tuple(flips), hits=hits, potency_before=potency_before)


__all__ = [
    "Action",
    "ActionResolution",
    "Card",
    "DEFAULT_DECK",
    "JeongSimulation",
    "KozanResult",
    "Suit",
    "TurnEndResult",
    "TurnSnapshot",
]
