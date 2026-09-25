# Salvage Above Venus

Missions for the **Above the Venusian Clouds** mod (`VenusClouds-Mod`, `venus_fleets`
v0.2.0). Pick one of the six factions, fly its cruiser, and keep your lift rings whole.

| Map | Goal |
|---|---|
| **Salvage Above Venus** | Harvest resource clouds, strip wrecks, and haul the cargo home before time runs out |
| **Fleet Battle Above Venus** | Destroy the enemy faction's command spire 26 km away; your fleet flies with you |
| **Convoy to the Yards** | Get at least two of your three barges and a tender 30 km to the Yards |
| **Siege of the Haven** | Hold your command spire against waves from every hostile faction |

## Salvage

- **Harvest.** Harvest ice, sulfur, ore, spores and aether in the resource clouds, and
  strip wrecks for salvage.
- **The hold.** It is limited by hull: a cruiser carries 250. A full hold means a trip
  home.
- **At a market station** (your Haven or the neutral Yards), open comms:
  - **Sell the hold** for credits. Selling also refits your lift rings.
  - **Trade cargo for refits**:

| Refit | Cost | Effect |
|---|---|---|
| Restock missiles | 40 fuel | refills every tube type |
| Refit lift rings | 20 aether | lift restored, shields charged |
| Enlarge the hold | 60 materials + 20 salvage | +100 hold, for good |
| Bolt on plating | 50 materials | shields to full |

- **Docking** at a market station also refits the rings: slower, but free.
- **The target** is 800 + 200 per difficulty level for one crew, and 70% more for each
  extra crew.
- **Raids** come in on a crew's flank, 5-7 km out, from factions hostile to yours. They
  grow every other wave, plus one ship per extra crew.
- **Wind lanes** run out from the Haven and back. Fly with the wind for 1.6x speed.
- **The Airship app** on the ePADD shows lift and hold and fires your faction's doctrine; its tile badge shows lift and whether the doctrine is ready.

## Settings and test hooks

| Setting | Where |
|---|---|
| Player ships, difficulty, faction, game length | each map's properties panel |
| `VS_FACTION_FORCE` / `VS_ENEMY_FORCE` | settings or profile: force a faction |
| `VS_TEST_CARGO` | test hook: start every hold with N coolant, sold automatically |
| `VS_AUTOPILOT` | balance hook: fly every crew out to clouds and home, log to `vs_balance.log` |

Profiles:

- `profiles/test_syndicate_win.yaml` runs the whole win path.
- `profiles/autopilot.yaml` runs a balance session.

Both work headless (`mission_runner ... --profile <name>`) and in the engine
(`profile=<name>`).

## Balance notes (autopilot sessions, 2026-09-24)

- **Session 1** (old rules): one cruiser carried 200 ore per trip (about 2.5 minutes a
  trip, about 640 credits) and won a 25-minute game in 8 minutes. The raiders never found
  it. That run led to the hold cap, the higher target, and flank raids.
- **Sessions 2 and 3** (new rules): a trip is 240 units for about 750 credits. Raids now
  reach the crew, and an autopilot that neither fights nor hides loses its rings within
  a few waves. That was also how a bug surfaced: a refit did not repair the ring rooms.
- **Still open:** judging raid size against a crew that shoots back. That needs a real
  crew.
