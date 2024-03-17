from models import Player, Tank, TankDetails, Canon, BaseAmmo
from math import tanh, asinh, exp
import datetime


def player_id_service(players: list[dict], nickname: str) -> int:
    for player in players:
        if player["nickname"] == nickname:
            return player["account_id"]
    return -1


def player_stats_service(data: dict) -> Player:
    nickname: str = data["nickname"]
    created_at: str = datetime.date.fromtimestamp(data["created_at"]).strftime("%Y-%m-%d")

    statistics = data["statistics"]["all"]
    battles: int = statistics["battles"]
    wins: int = statistics["wins"]
    survived: int = statistics["survived_battles"]
    losses: int = statistics["losses"]
    draws: int = statistics["draws"]
    wins_percents: float = wins / battles if battles != 0 else 0.0
    avg_dmg: float = statistics["damage_dealt"] / battles if battles != 0 else 0.0
    avg_dmg_assist_radio: float = statistics["avg_damage_assisted_radio"]
    avg_dmg_assist_track: float = statistics["avg_damage_assisted_track"]
    avg_dmg_blocked: float = statistics["avg_damage_blocked"]
    battle_avg_xp: float = statistics["battle_avg_xp"]
    hits_percents: float = statistics["hits_percents"]
    frags: int = statistics["frags"]
    max_frags: int = statistics["max_frags"]
    max_xp: int = statistics["max_xp"]

    personal_rating: int = 0 if battles == 0 else calculate_personal_rating(
        battles, wins / battles, survived / battles, avg_dmg, battle_avg_xp, avg_dmg_assist_radio, avg_dmg_assist_track
    )
    return Player(
        nickname=nickname,
        created_at=created_at,
        battles=battles,
        wins=wins,
        losses=losses,
        draws=draws,
        wins_percents=round(wins_percents, 2),
        avg_dmg=round(avg_dmg, 2),
        avg_dmg_assist_radio=avg_dmg_assist_radio,
        avg_dmg_assist_track=avg_dmg_assist_track,
        avg_dmg_blocked=avg_dmg_blocked,
        battle_avg_xp=battle_avg_xp,
        hits_percents=round(hits_percents, 2),
        frags=frags,
        max_frags=max_frags,
        max_xp=max_xp,
        personal_rating=personal_rating
    )


def tanks_list_service(tanks_list: dict) -> list[Tank]:
    final_list: list[Tank] = []
    tank_keys: list[str] = list(tanks_list.keys())

    for key in tank_keys:
        tanks_data: dict = tanks_list[key]
        tank_id = tanks_data["tank_id"]
        new_tank: Tank = Tank(
            tank_id=tank_id,
            name=tanks_data["name"],
            tank_type=tanks_data["type"],
            nation=tanks_data["nation"],
            tier=tanks_data["tier"],
            tank_img_url=tanks_data["images"]["big_icon"],
            action=f"/main/tanks_list/{tank_id}",
            description=tanks_data["description"]
        )
        final_list.append(new_tank)

    return final_list


def tank_details_service(
        tank_details: dict, tank_name: str, tank_type: str, nation: str, tier, tank_img_url: str, description: str
) -> TankDetails:
    hp: int = tank_details["hp"]
    speed_forward: int = tank_details["speed_forward"]
    speed_backward: int = tank_details["speed_backward"]
    canon: Canon = get_top_canon(tank_details["gun"])
    base_ammo: BaseAmmo = get_base_ammo(tank_details["ammo"][0])

    return TankDetails(
        name=tank_name,
        tank_type=tank_type,
        nation=nation,
        tier=tier,
        tank_img_url=tank_img_url,
        description=description,
        hp=hp,
        speed_forward=speed_forward,
        speed_backward=speed_backward,
        canon=canon,
        base_ammo=base_ammo
    )


def get_top_canon(gun_data: dict) -> Canon:
    move_down_arc: float = gun_data["move_down_arc"]
    move_up_arc: float = gun_data["move_up_arc"]
    caliber: float = gun_data["caliber"]
    name: str = gun_data["name"]
    reload_time: float = gun_data["reload_time"]
    aim_time: float = gun_data["aim_time"]
    dispersion: float = gun_data["dispersion"]
    return Canon(
        move_down_arc=move_down_arc,
        move_up_arc=move_up_arc,
        caliber=caliber,
        name=name,
        reload_time=reload_time,
        aim_time=aim_time,
        dispersion=dispersion
    )


def get_base_ammo(ammo_data: dict) -> BaseAmmo:
    min_pen: int = ammo_data["penetration"][0]
    avg_pen: int = ammo_data["penetration"][1]
    max_pen: int = ammo_data["penetration"][2]
    min_dmg: int = ammo_data["damage"][0]
    avg_dmg: int = ammo_data["damage"][1]
    max_dmg: int = ammo_data["damage"][2]
    return BaseAmmo(
        min_pen=min_pen,
        avg_pen=avg_pen,
        max_pen=max_pen,
        min_dmg=min_dmg,
        avg_dmg=avg_dmg,
        max_dmg=max_dmg
    )


def calculate_personal_rating(
        battles: int,
        wins_ratio: float,
        survived_ratio: float,
        avg_dmg: float,
        avg_xp: float,
        radio_assist: float,
        track_assist: float
) -> int:
    bc_factor_1 = 540 * (battles ** 0.37)
    bc_factor_2 = 0.00163 * (battles ** (-0.37))
    wins_factor = 3500 / (1 + exp(16 - 31 * wins_ratio))
    survived_factor = 1400 / (1 * exp(8 - 27 * survived_ratio))
    dmg_factor = 3700 * asinh(0.0006 * avg_dmg)
    xp_factor = 3900 * asinh(0.0015 * avg_xp)
    assist_factor_1 = 1.4 * radio_assist
    assist_factor_2 = 1.1 * track_assist

    personal_rate = bc_factor_1 * tanh(
        bc_factor_2 * (wins_factor + survived_factor + dmg_factor + xp_factor + assist_factor_1 + assist_factor_2)
    )
    return round(personal_rate)

