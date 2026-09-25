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
    _vs("venus_lift_refit")(player)
    return value


def vs_sell_offer(player):
    """What this crew's hold would sell for, in credits."""
    from sbs_utils.procedural.query import to_object
    p = to_object(player)
    if p is None:
        return 0
    return int(sum(VS_PRICES.get(k, 1) * v for k, v in _vs("venus_cargo")(p).items()))


def vs_sell_range():
    return VS_SELL_RANGE


def vs_test_cargo(units):
    """TEST HOOK (profile var VS_TEST_CARGO): start every hold with this much coolant, so
    the sell and win path can be exercised without flying. Once per ship - called from the
    loop, since a crew can be re-hulled after the map body ran."""
    from sbs_utils.procedural.roles import role
    from sbs_utils.procedural.query import to_object_list
    from sbs_utils.procedural.inventory import set_inventory_value, get_inventory_value
    if not units or units <= 0:
        return 0
    for p in to_object_list(role("__player__")):
        if p is not None and not get_inventory_value(p.id, "vs_test_seeded", False):
            set_inventory_value(p.id, "vs_test_seeded", True)
            set_inventory_value(p.id, "venus_cargo_coolant", float(units))
    return units


def vs_cargo_text(player):
    cargo = _vs("venus_cargo")(player)
    if not cargo:
        return "hold empty"
    return ", ".join(str(v) + " " + k for k, v in sorted(cargo.items()))


# BALANCE (autopilot session, 2026-09-24): one cruiser hauling 200 ore a trip won a
# 25-minute game in 8 minutes against a flat 600 + 150/difficulty, and no raider ever found
# it. So the target grows with difficulty AND the number of crews hauling, and raids come
# in on a crew's flank instead of at a random point on a 14 km ring.
def vs_target(difficulty):
    """Credits to win: (800 + 200 per difficulty) for one crew, +70% per extra crew."""
    from sbs_utils.procedural.roles import role
    from sbs_utils.procedural.query import to_object_list
    crews = max(1, len([p for p in to_object_list(role("__player__")) if p is not None]))
    one = 800 + 200 * max(1, int(difficulty))
    return int(round(one * (1 + 0.7 * (crews - 1)) / 50.0) * 50)


def vs_raid_size(difficulty, wave):
    """Fleet size for raid `wave`: grows every OTHER wave, plus one per extra crew.
    Session 2 (2026-09-24) sent 3,4,5,6,7 at a lone cruiser every three minutes and
    stripped its rings by the fourth wave."""
    from sbs_utils.procedural.roles import role
    from sbs_utils.procedural.query import to_object_list
    crews = max(1, len([p for p in to_object_list(role("__player__")) if p is not None]))
    return max(1, min(10, int(difficulty) // 3 + (int(wave) + 1) // 2 + (crews - 1)))


def vs_dock_refit(player):
    """A crew DOCKED at a market yard gets its lift rings refitted - the free way back to
    full lift (selling and the rings trade are the quick ways)."""
    from sbs_utils.procedural.roles import has_role
    from sbs_utils.procedural.query import get_data_set_value
    if player is None:
        return False
    if get_data_set_value(player.id, "dock_state", default="") != "docked":
        return False
    base = get_data_set_value(player.id, "dock_base_id", default=0) or 0
    if not base or not has_role(base, "vs_market"):
        return False
    if _vs("venus_lift_get")(player) < 1.0:
        _vs("venus_lift_refit")(player)
        return True
    return False


def vs_raid_point():
    """Where a raid wave arrives: 5-7 km off a random crew, so it has something to hunt."""
    import math
    import random
    from sbs_utils.procedural.roles import role
    from sbs_utils.procedural.query import to_object_list
    ps = [p for p in to_object_list(role("__player__")) if p is not None]
    a = random.uniform(0, 2 * math.pi)
    d = random.uniform(5000, 7000)
    cx, cz = 0.0, 0.0
    if ps:
        p = random.choice(ps)
        cx, cz = p.pos.x, p.pos.z
    return _vs_vec(cx + math.cos(a) * d, 0, cz + math.sin(a) * d)


def vs_wind_lanes(count=3, reach=26000.0):
    """Fast lanes out from the Haven and back: `count` outbound, `count` inbound, spread
    around the compass. Wind lanes are the mod's (venus_wind_lane)."""
    import math
    import random
    lane = _vs("venus_wind_lane")
    n = 0
    base = random.uniform(0, 2 * math.pi)
    for i in range(count * 2):
        a = base + i * math.pi / count
        near, far = 2500.0, reach
        x0, z0 = math.cos(a) * near, math.sin(a) * near
        x1, z1 = math.cos(a) * far, math.sin(a) * far
        if i % 2:
            x0, z0, x1, z1 = x1, z1, x0, z0      # inbound: blows toward home
        n = lane(x0, z0, x1, z1, 0.0, 1400.0)
    return n


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


# --------------------------------------------------------------------------- trade
# Cargo spent at a market yard on refits instead of sold for credits - the choice between
# winning faster and surviving longer. name -> (label, {resource: units}, what it does)
VS_TRADES = {
    "missiles": ("Restock missiles", {"fuel": 40}, "every tube type refilled"),
    "rings":    ("Refit lift rings", {"aether": 20}, "lift restored and shields charged"),
    "hold":     ("Enlarge the hold", {"materials": 60, "salvage": 20}, "+100 hold, for good"),
    "armor":    ("Bolt on plating", {"materials": 50}, "shields to full"),
}


def _vs_cost_text(cost):
    return ", ".join(str(v) + " " + k for k, v in cost.items())


def vs_trade_can(ship, key):
    from sbs_utils.procedural.query import to_object
    ship = to_object(ship)
    if ship is None or key not in VS_TRADES:
        return False
    cargo = _vs("venus_cargo")(ship)
    return all(cargo.get(k, 0) >= v for k, v in VS_TRADES[key][1].items())


def vs_trade_label(key):
    label, cost, what = VS_TRADES[key]
    return label + " (" + _vs_cost_text(cost) + ")"


def vs_trade(ship, key):
    """Spend cargo on a refit. Returns a line for comms (ASCII, brace-free)."""
    from sbs_utils.procedural.query import to_object
    from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
    ship = to_object(ship)
    if not vs_trade_can(ship, key):
        return "Not enough cargo for that."
    label, cost, what = VS_TRADES[key]
    for k, v in cost.items():
        have = get_inventory_value(ship.id, "venus_cargo_" + k, 0.0) or 0.0
        set_inventory_value(ship.id, "venus_cargo_" + k, max(0.0, have - v))
    if key == "missiles":
        from sbs_utils.procedural.torpedoes import torpedo_get_available_types_for_ship
        from sbs_utils.procedural.query import get_data_set_value, set_data_set_value
        for t in torpedo_get_available_types_for_ship(ship.id) or []:
            top = get_data_set_value(ship.id, t + "_MAX", default=None)
            if top is not None:
                set_data_set_value(ship.id, t + "_NUM", top)
    elif key == "rings":
        _vs("venus_lift_refit")(ship)
        _vs_shields(ship)
    elif key == "hold":
        set_inventory_value(ship.id, "venus_hold_bonus", (get_inventory_value(ship.id, "venus_hold_bonus", 0) or 0) + 100)
    elif key == "armor":
        _vs_shields(ship)
    vs_balance_note("TRADE " + key)
    return label + " done - " + what + "."


def _vs_shields(ship):
    ds = ship.data_set
    for i in range(4):
        try:
            top = ds.get("shield_max_val", i)
            if top is not None:
                ds.set("shield_val", top, i)
        except Exception:
            pass


# --------------------------------------------------------------------------- autopilot
# BALANCE HOOK (setting VS_AUTOPILOT): fly every crew through the loop a player would -
# out to the nearest resource cloud, harvest until the hold is full or the cloud is gone,
# home to a market, sell - and log each leg with sim time to vs_balance.log. A stand-in
# for a playthrough, so prices, the target and the raid clock can be tuned from numbers.
VS_AUTOPILOT_FILL = 0.95            # fraction of the hold the autopilot fills before heading home


def _vs_log(text):
    from sbs_utils.fs import get_mission_dir_filename
    from sbs_utils.helpers import FrameContext
    try:
        with open(get_mission_dir_filename("vs_balance.log"), "a") as fh:
            fh.write("%7.1f %s\n" % (FrameContext.sim_seconds or 0.0, text))
    except Exception:
        pass


def vs_balance_note(text):
    """A line in vs_balance.log - only while the autopilot is on."""
    if vs_setting("VS_AUTOPILOT", 0):
        _vs_log(str(text))
    return True


def vs_autopilot_reset():
    from sbs_utils.fs import get_mission_dir_filename
    try:
        open(get_mission_dir_filename("vs_balance.log"), "w").close()
    except Exception:
        pass


def _vs_nearest(ship, objs):
    from sbs_utils.procedural.helm import helm_distance
    best, bd = None, float("inf")
    for o in objs:
        d = helm_distance(ship, o)
        if d < bd:
            best, bd = o, d
    return best, bd


def vs_autopilot_step(ship):
    """One 3-second decision for one crew. State lives on the ship's inventory."""
    from sbs_utils.procedural.roles import role
    from sbs_utils.procedural.query import to_object_list, to_object
    from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
    from sbs_utils.procedural.helm import helm_steer_to_point, helm_throttle, helm_stop
    if ship is None:
        return
    state = get_inventory_value(ship.id, "vs_ap_state", "out")
    held = sum(_vs("venus_cargo")(ship).values())
    lift = _vs("venus_lift_get")(ship)
    if state == "out":
        clouds = [c for c in to_object_list(role("venus_cloud"))
                  if c is not None and get_inventory_value(c.id, "venus_resource", None)
                  and (get_inventory_value(c.id, "venus_stock", 0) or 0) > 0]
        cloud, d = _vs_nearest(ship, clouds)
        if held >= VS_AUTOPILOT_FILL * _vs("venus_hold_capacity")(ship) or (cloud is None and held > 0)                 or (lift < 0.35 and held > 0):
            set_inventory_value(ship.id, "vs_ap_state", "home")
            _vs_log("%s heading home: hold %d lift %.2f" % (ship.name, held, lift))
            return
        if cloud is None:
            helm_stop(ship)
            return
        if get_inventory_value(ship.id, "vs_ap_cloud", 0) != cloud.id:
            set_inventory_value(ship.id, "vs_ap_cloud", cloud.id)
            _vs_log("%s -> %s (%s) at %.0f" % (ship.name, cloud.name, get_inventory_value(cloud.id, "venus_resource", ""), d))
        r = get_inventory_value(cloud.id, "venus_radius", 300) or 300
        helm_steer_to_point(ship, cloud)
        helm_throttle(ship, 1.0 if d > r * 0.5 else 0.0, allow_warp=False)
    else:
        home, d = _vs_nearest(ship, [s for s in to_object_list(role("vs_market")) if s is not None])
        if home is None:
            return
        if d > VS_SELL_RANGE * 0.6:
            helm_steer_to_point(ship, home)
            helm_throttle(ship, 1.0, allow_warp=False)
        else:
            helm_stop(ship)
            if held <= 0:
                set_inventory_value(ship.id, "vs_ap_state", "out")
                set_inventory_value(ship.id, "vs_ap_cloud", 0)


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
