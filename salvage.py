# Salvage Above Venus - mission helpers. vs_-prefixed: every public function here becomes a
# MAST global. The mod's own functions (venus_*) are MAST globals too, but this file's
# Python cannot see them directly - _vs() looks them up where MAST registered them.

# What a unit of each harvested resource sells for at home.
VS_PRICES = {"coolant": 1, "fuel": 2, "materials": 3, "medicine": 3, "salvage": 5, "aether": 8}
VS_SELL_RANGE = 900.0


def _vs(name):
    from sbs_utils.mast.mast_globals import MastGlobals
    return MastGlobals.globals[name]


def vs_race(race):
    """The canonical faction name for whatever the dropdown handed us."""
    races = _vs("venus_races")()
    for r in races:
        if str(race).strip().lower() == r.lower():
            return r
    return races[0] if races else "Flotilla"


def vs_seat(race):
    """Seat every player crew in their faction's cruiser, on their faction's side - the
    same re-hull the library's roster does (art_id, then rebuild the stats)."""
    from sbs_utils.procedural.roles import role
    from sbs_utils.procedural.query import to_object_list
    from sbs_utils.procedural.player_roster import player_ship_rebuild_stats
    race = vs_race(race)
    fac = _vs("venus_faction_info")(race) or {}
    hull = "venus_" + fac.get("tag", "steam") + "_cruiser"
    n = 0
    for p in to_object_list(role("__player__")):
        if p is None:
            continue
        if p.art_id != hull:
            p.art_id = hull
            player_ship_rebuild_stats(p)
        p.side = race.lower()
        n += 1
    return n


def vs_home_spawn(race):
    """Home: the faction's civil station at the origin, and a neutral industrial yard that
    also buys. Returns the home station's id."""
    from sbs_utils.procedural.spawn import npc_spawn
    from sbs_utils.procedural.query import to_id
    race = vs_race(race)
    fac = _vs("venus_faction_info")(race) or {}
    tag = fac.get("tag", "steam")
    home = to_id(npc_spawn(0, 0, 0, fac.get("name", race) + " Haven", race.lower() + ", station, vs_market",
                           "venus_" + tag + "_station_civil", "behav_station"))
    other = "Commons" if race != "Commons" else "Concord"
    ofac = _vs("venus_faction_info")(other) or {}
    npc_spawn(6000, 400, -3500, ofac.get("name", other) + " Yards", other.lower() + ", station, vs_market",
              "venus_" + ofac.get("tag", "solar") + "_station_industrial", "behav_station")
    return home


def vs_place_players(home_id):
    """Put the crews just off their home station."""
    from sbs_utils.procedural.roles import role
    from sbs_utils.procedural.query import to_object_list, to_object
    home = to_object(home_id)
    for i, p in enumerate(to_object_list(role("__player__"))):
        if p is not None and home is not None:
            p.pos = home.pos + _vs_vec(350 + i * 250, 0, 550)
    return True


def _vs_vec(x, y, z):
    from sbs_utils.vec import Vec3
    return Vec3(x, y, z)


def vs_sell(player):
    """Sell a crew's hold at any market station in range. Returns the credits earned (0
    when out of range or empty). Selling also refits the lift rings to full."""
    from sbs_utils.procedural.roles import role
    from sbs_utils.procedural.query import to_object_list
    from sbs_utils.procedural.inventory import set_inventory_value
    from sbs_utils.procedural.execution import get_shared_variable, set_shared_variable
    if player is None:
        return 0
    near = False
    for st in to_object_list(role("vs_market")):
        if st is None:
            continue
        d = ((st.pos.x - player.pos.x) ** 2 + (st.pos.y - player.pos.y) ** 2 + (st.pos.z - player.pos.z) ** 2) ** 0.5
        if d <= VS_SELL_RANGE:
            near = True
            break
    if not near:
        return 0
    cargo = _vs("venus_cargo")(player)
    value = sum(VS_PRICES.get(k, 1) * v for k, v in cargo.items())
    if value <= 0:
        return 0
    for k in cargo:
        set_inventory_value(player.id, "venus_cargo_" + k, 0.0)
    set_shared_variable("VS_CREDITS", (get_shared_variable("VS_CREDITS") or 0) + value)
    _vs("venus_lift_set")(player, 1.0)
    return value


def vs_test_cargo(units):
    """TEST HOOK (profile var VS_TEST_CARGO): start every hold with this much coolant, so
    the sell and win path can be exercised without flying."""
    from sbs_utils.procedural.roles import role
    from sbs_utils.procedural.query import to_object_list
    from sbs_utils.procedural.inventory import set_inventory_value
    for p in to_object_list(role("__player__")):
        if p is not None:
            set_inventory_value(p.id, "venus_cargo_coolant", float(units))
    return units


def vs_cargo_text(player):
    cargo = _vs("venus_cargo")(player)
    if not cargo:
        return "hold empty"
    return ", ".join(str(v) + " " + k for k, v in sorted(cargo.items()))


def vs_enemy_races(race):
    """The factions hostile to this one, from the mod's own diplomacy."""
    from sbs_utils.procedural.sides import side_are_enemies
    race = vs_race(race)
    return [r for r in _vs("venus_races")() if r != race and side_are_enemies(race.lower(), r.lower())]


def vs_setting(key, default=None):
    """A value from settings.yaml / the active profile (settings are not MAST variables)."""
    from sbs_utils.procedural.settings import settings_get_defaults
    v = (settings_get_defaults() or {}).get(key)
    return default if v is None else v


def vs_int(value, default):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def vs_report():
    """One status line in vs_status.txt for engine runs (the engine hands back no stdout)."""
    from sbs_utils.procedural.execution import get_shared_variable
    from sbs_utils.procedural.roles import role
    from sbs_utils.procedural.query import to_object_list
    from sbs_utils.fs import get_mission_dir_filename
    ps = [p for p in to_object_list(role("__player__")) if p is not None]
    line = "credits %s/%s faction %s players %s" % (get_shared_variable("VS_CREDITS"), get_shared_variable("VS_TARGET"),
                                                  get_shared_variable("VS_FACTION"),
                                                  [(p.art_id, p.side, vs_cargo_text(p)) for p in ps])
    try:
        with open(get_mission_dir_filename("vs_status.txt"), "w") as fh:
            fh.write(line + "\n")
    except Exception:
        pass
    return line
