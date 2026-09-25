# Salvage Above Venus

A salvage-and-survival mission for the **Above the Venusian Clouds** mod
(`VenusClouds-Mod`, `venus_fleets` v0.2.0).

Pick one of the six factions and fly its cruiser out of your home **Haven**. Harvest the
resource clouds (ice, sulfur, ore, spores, aether), strip the wrecks for salvage, and sell
everything at a market station - your Haven or the neutral industrial yard. Selling also
refits your lift rings. Reach the credit target before time runs out.

Against you: raider waves from whichever factions are hostile to yours (bigger each wave),
storm cells that tear at your rings, and the deck itself - a ship that loses its lift sinks.
Hiding inside a cloud keeps raiders' missiles off you.

| Setting | Where |
|---|---|
| Player ships, difficulty, faction, game length | the map's properties panel |
| `VS_FACTION_FORCE` | settings / profile: force a faction |
| `VS_TEST_CARGO` | test hook: start every hold with N units of coolant |

`profiles/test_syndicate_win.yaml` exercises the whole win path in the engine:
`Artemis3-x64-release.exe autostartserver defaultmission=VenusSalvage map=venus_salvage profile=test_syndicate_win`
