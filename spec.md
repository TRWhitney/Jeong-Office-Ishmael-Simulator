# SPEC — Jeong Office Ishmael (Limbus Company) Simulation
Audience: AI agent (Codex/GPT-5) acting as the programmer
Goal: Build a simplified, faithful simulator so a user can practice optimal play with Jeong Office Ishmael
Constraints: Language/OS agnostic. No speed dice/turn order. Include a skill deck. Offers persist across turns.

--------------------------------------------------------------------------------
## 1) Entities and State

### 1.1 Identity (Ishmael)
- Skills (fixed colors): **S1 → Red**, **S2 → Yellow**, **S3 → Blue**
- Defensive Skill: **Counter**
- **EGO**: action that **always matches the current suit’s color**

### 1.2 Suit
- `currentSuit ∈ {Red, Yellow, Blue}`
- Assigned at **combat start** and on **Bright cycle reset**

### 1.3 Bright
- `brightPotency ∈ [0..5]` (cap 5)
- `brightCount ∈ [0..3]` (starts 3)
- Decrement `brightCount` **at end of each turn**
- Cycle ends when `brightPotency == 5` **or** `brightCount == 0`

### 1.4 Deck and Offer (hand)
- Deck per rotation (default): `[S1, S1, S1, S2, S2, S3]`
- Shuffle at battle start and when exhausted
- **Offer persists** across turns; it is an **ordered** list of up to 2 cards:
  - At **start of turn**, **refill** to 2 by drawing from deck
  - **Index 0 = first**, **Index 1 = second**
  - When the **first** card is **used or discarded**, the **second becomes the first** (shift left)

### 1.5 Minimum State
- `currentSuit`, `brightPotency`, `brightCount`
- `deck`, `discardPile`, `offer` (ordered, size ≤ 2, persists)
- `rngSeed` (optional)

--------------------------------------------------------------------------------
## 2) Turn Flow

1) If a cycle just reset: `currentSuit ← random{Red, Yellow, Blue}`
2) Refill `offer` to size 2 from `deck` (reshuffle when empty)
3) Present actions: **Use First (offer[0])**, **Use Second (offer[1], if present)**, **Defend**, **EGO**
4) Resolve the chosen action (apply §3)
5) End of turn: `brightCount -= 1`; check finisher (§3.6)

--------------------------------------------------------------------------------
## 3) Mechanics

### 3.1 Matching
- **Match** if action color == `currentSuit`; else **Mismatch**

### 3.2 Bright gain
- On **Match** with S1/S2/S3: `brightPotency += 1` (cap 5)
- **S3 bonus**: whenever **S3** is used (match or mismatch), add **`+1` additional Potency** (cap 5)
- **EGO**: always counts as matching; grant **`+2` Potency** (cap 5)
- If previous turn also matched within the same cycle, add **`+1`**
- On other **Mismatch** cases: `+0`

### 3.3 Jeong attack discard (offer persistence + ordering)
After **using** an offered **attack** card (from either slot):
- Remove the **used** card from `offer` → discard
- If one card remains in `offer`:
  - If its **color ≠ used card’s color** → **discard it now**
  - If its **color = used card’s color** → **keep it**
- After any removal, **shift** so the remaining card (if any) is `offer[0]`

### 3.4 Defend (Counter)
- Uses the turn; no attack
- **50%** chance: `brightPotency += 1` (cap 5)
- **Discard the first choice**: if `offer.size ≥ 1`, discard `offer[0]` (then shift)
- **Suit shuffle**: assign a **new random Suit next turn**

### 3.5 EGO
- Always matches `currentSuit`
- **Bright on use**: `brightPotency += 2` (cap 5)
- **Discard the first choice**: if `offer.size ≥ 1`, discard `offer[0]` (then shift)

### 3.6 Finisher: **Kōzan**
- Check **after** action resolution and `brightCount` decrement:
  - If `brightPotency == 5` **or** `brightCount == 0`:
    - If `brightPotency ≥ 3`: **Kōzan activates**
      - **Independent coin flips**: `flips = min(brightPotency, 5)`
      - Each flip is independent with **Heads probability = 95%**
      - Total hits = number of Heads across all flips (no stopping on Tails)
      - Log sequence (e.g., “H, H, T, H, H → 4 hits”)
    - Else: **no effect**
    - **Reset Bright cycle**: `brightPotency = 0`, `brightCount = 3`, `currentSuit = random{Red,Yellow,Blue}`

--------------------------------------------------------------------------------
## 4) Pseudocode (language-agnostic)

Initialization:
- `deck = shuffle([S1,S1,S1,S2,S2,S3])`
- `offer = []`
- `currentSuit = randomColor()`
- `brightPotency = 0`, `brightCount = 3`

StartOfTurn():
- while `offer.size < 2`:
  - if `deck.empty`: `deck = shuffle([S1,S1,S1,S2,S2,S3])`
  - `offer.push(pop(deck))`
- show: Suit, Potency, Count, Offer (First/Second), Actions: Use First, Use Second, Defend, EGO

UseAttack(idx):
- `card = offer[idx]`; `usedColor = color(card)`
- if `usedColor == currentSuit`: `brightPotency = min(5, brightPotency + 1)`
- if `card == S3`: `brightPotency = min(5, brightPotency + 1)`   // S3 extra potency
- remove `offer[idx]` → discard; shift
- if `offer.size == 1` and `color(offer[0]) != usedColor`: discard `offer[0]`; `offer = []`

Defend():
- if `rand() < 0.5`: `brightPotency = min(5, brightPotency + 1)`
- if `offer.size ≥ 1`: discard `offer[0]`; shift
- flag: next turn suit shuffle (set `currentSuit = randomColor()` at next start)

EGO():
- `brightPotency = min(5, brightPotency + 2)`    // always matches
- if `offer.size ≥ 1`: discard `offer[0]`; shift

EndOfTurn():
- `brightCount -= 1`
- if (`brightPotency == 5`) or (`brightCount == 0`):
  - if `brightPotency >= 3`: `performKozan(brightPotency)` else no-op
  - `brightPotency = 0`; `brightCount = 3`; `currentSuit = randomColor()`

performKozan(p):
- `flips = min(p, 5)`; `hits = 0`; `seq = []`
- repeat `flips` times:
  - `c = (rand() < 0.95) ? 'H' : 'T'`
  - append `c` to `seq`
  - if `c == 'H'`: `hits += 1`
- log: “Kōzan → {seq} → Hits: {hits}”

--------------------------------------------------------------------------------
## 5) I/O (per turn)

Pre-choice:
- Current Suit; Bright Potency/Count
- Offer: First (name+color), Second (name+color); mark persisted cards
- Actions: Use First, Use Second, Defend, EGO

Post-resolution:
- Action taken; **Matched/Mismatched**
- Bright delta; new Potency/Count
- Offer edits: used card removed; off-color discard (if any); **second→first shift** (if applicable)
- If Kōzan: coin sequence and hits
- If cycle reset: “New Suit next turn”

--------------------------------------------------------------------------------
## 6) Acceptance Checklist
- [x] Offer persists; refill to 2 at start; **second becomes first** whenever the first is used or discarded
- [x] Attack use: unpicked card discarded iff its color ≠ used card’s color; same-color persists
- [x] Defend: discards first; 50% Bright +1; suit shuffles next turn
- [x] EGO: always matches Suit; discards first; **Bright +2**
- [x] S3 grants **+1 extra Potency on use** (in addition to any match Potency)
- [x] Cycle ends at Potency==5 or Count==0; **Kōzan uses independent flips (p(Heads)=0.95) and totals Heads**; cycle resets and Suit re-assigned
