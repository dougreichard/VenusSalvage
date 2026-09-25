# Helpers for the three operations maps (venus_ops.mast): fleet battle, convoy, siege.
# vs_-prefixed like salvage.py - every public function here is a MAST global. The
# underscore helpers are this file's own: a leading underscore is private to its FILE, so
# salvage.py's _vs / _vs_vec are not visible here.


def _vs(name):
    from sbs_utils.mast.mast_globals import MastGlobals
    return MastGlobals.globals[name]


def _vs_vec(x, y, z):
    from sbs_utils.vec import Vec3
    return Vec3(x, y, z)


def vs_ops_enemy(race, pick=None):
    """A hostile faction for `race`: `pick` when given and different, else the first hostile
    one. Makes the two hostile if the mod's diplomacy did not."""
    import sbs
    from sbs_utils.procedural.sides import side_are_enemies, side_set_relations
    race = vs_race(race)
    races = _vs("venus_races")()
    enemy = vs_race(pick) if pick else None
    if enemy is None or enemy == race:
        hostile = vs_enemy_races(race)
        enemy = hostile[0] if hostile else next(r for r in races if r != race)
    if not side_are_enemies(race.lower(), enemy.lower()):
        side_set_relations(race.lower(), enemy.lower(), sbs.DIPLOMACY.HOSTILE)
    return enemy


def vs_ops_station(race, kind, x, y, z, extra=""):
    """Spawn a faction station (command / industrial / civil / science). Returns its id."""
    from sbs_utils.procedural.spawn import npc_spawn
    from sbs_utils.procedural.query import to_id
    race = vs_race(race)
    fac = _vs("venus_faction_info")(race) or {}
    names = {"command": "Spire", "industrial": "Yards", "civil": "Haven", "science": "Observatory"}
    roles = race.lower() + ", station" + ("," + extra if extra else "")
    return to_id(npc_spawn(x, y, z, fac.get("name", race) + " " + names.get(kind, kind.title()), roles,
                           "venus_" + fac.get("tag", "steam") + "_station_" + kind, "behav_station"))


def vs_ops_brain(target_roles):
    """A raider fleet brain that hunts `target_roles` first, then players - the same tree
    as LegendaryMissions' prefab_fleet_raider with the target swapped."""
    return {"SEQ Movement": [
        "ai_fleet_init_blackboard",
        {"SEL Choose Target": [
            {"label": "ai_fleet_chase_roles", "data": {"test_roles": target_roles, "use_arena": False}},
            {"label": "ai_fleet_chase_roles", "data": {"test_roles": "__player__", "use_arena": False}},
            {"label": "ai_fleet_chase_roles", "data": {"test_roles": "station", "use_arena": False}},
        ]},
        "ai_fleet_calc_forward_vector",
        "ai_fleet_scatter_formation",
    ]}


def vs_ops_fleet_data(race, size, pos, brain=None):
    """The prefab_fleet_raider data for a faction fleet at `pos` (a Vec3)."""
    d = {"race": vs_race(race), "fleet_difficulty": max(1, min(10, int(size))), "faction_side": True,
         "START_X": pos.x, "START_Y": pos.y, "START_Z": pos.z}
    if brain is not None:
        d["brain"] = brain
    return d


def vs_ops_near(center_id, lo, hi):
    """A random point lo..hi from an object (or the origin when it is gone)."""
    import math
    import random
    from sbs_utils.procedural.query import to_object
    o = to_object(center_id) if center_id else None
    cx, cz = (o.pos.x, o.pos.z) if o is not None else (0.0, 0.0)
    a = random.uniform(0, 2 * math.pi)
    d = random.uniform(lo, hi)
    return _vs_vec(cx + math.cos(a) * d, 0, cz + math.sin(a) * d)


# --------------------------------------------------------------------------- convoy
def vs_convoy_spawn(race, x, z, barges=3, tenders=1):
    """The convoy: cargo barges and a tender of your faction, role vs_convoy. Returns ids."""
    from sbs_utils.procedural.spawn import npc_spawn
    from sbs_utils.procedural.query import to_id
    race = vs_race(race)
    fac = _vs("venus_faction_info")(race) or {}
    tag = fac.get("tag", "steam")
    ids = []
    for i in range(barges + tenders):
        design = "cargo_barge" if i < barges else "steam_tender"
        label = ("Barge " + str(i + 1)) if i < barges else ("Tender " + str(i - barges + 1))
        ids.append(to_id(npc_spawn(x + (i - 1.5) * 350, 0, z - i * 250, fac.get("name", race) + " " + label,
                                   race.lower() + ", vs_convoy", "venus_" + tag + "_" + design, "behav_npcship")))
    return [i for i in ids if i]


def vs_convoy_steer(ids, dest_id, throttle=0.7):
    """Keep every convoy ship heading for the destination; stop the ones that arrived.
    Returns (arrived, still_alive_en_route)."""
    from sbs_utils.procedural.query import to_object
    from sbs_utils.procedural.roles import has_role, add_role, remove_role
    from sbs_utils.procedural.space_objects import target_pos
    dest = to_object(dest_id)
    arrived = 0
    en_route = 0
    for i in ids:
        s = to_object(i)
        if s is None:
            continue
        if has_role(i, "vs_arrived"):
            arrived += 1
            continue
        if dest is None:
            en_route += 1
            continue
        d = ((s.pos.x - dest.pos.x) ** 2 + (s.pos.z - dest.pos.z) ** 2) ** 0.5
        if d < 1500:
            add_role(i, "vs_arrived")
            remove_role(i, "vs_convoy")
            target_pos(i, s.pos.x, s.pos.y, s.pos.z, 0.0)
            arrived += 1
        else:
            target_pos(i, dest.pos.x, dest.pos.y, dest.pos.z, throttle)
            en_route += 1
    return arrived, en_route


def vs_convoy_lead(ids):
    """The convoy ship still en route that is furthest along (for spawning raids ahead)."""
    from sbs_utils.procedural.query import to_object
    from sbs_utils.procedural.roles import has_role
    best = None
    for i in ids:
        s = to_object(i)
        if s is not None and not has_role(i, "vs_arrived"):
            if best is None or s.pos.z > to_object(best).pos.z:
                best = i
    return best


def vs_first(pair, index):
    return pair[index]
