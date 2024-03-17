from pydantic import BaseModel


class Player(BaseModel):
    nickname: str
    created_at: str
    battles: int
    wins: int
    losses: int
    draws: int
    wins_percents: float
    avg_dmg: float
    avg_dmg_assist_radio: float
    avg_dmg_assist_track: float
    avg_dmg_blocked: float
    battle_avg_xp: float
    hits_percents: float
    frags: int
    max_frags: int
    max_xp: int
    personal_rating: int


class Tank(BaseModel):
    tank_id: int = None
    name: str = None
    tank_type: str = None
    nation: str = None
    tier: int = None
    tank_img_url: str
    action: str = None
    description: str = None


class Canon(BaseModel):
    move_down_arc: float
    move_up_arc: float
    caliber: float
    name: str
    reload_time: float
    aim_time: float
    dispersion: float


class BaseAmmo(BaseModel):
    min_pen: int
    avg_pen: int
    max_pen: int
    min_dmg: int
    avg_dmg: int
    max_dmg: int


class TankDetails(Tank):
    hp: int
    speed_forward: int
    speed_backward: int
    canon: Canon
    base_ammo: BaseAmmo

