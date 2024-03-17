from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login import LoginManager
from models import Player, Tank, TankDetails
from services import player_stats_service, player_id_service, tanks_list_service, tank_details_service
from typing import Annotated
import json
import uvicorn
import httpx


SECRET = "secret"
DB = {
    "grzegorz": {
        "password": "12345"
    }
}

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

with open("api_token.json") as f:
    wot_api_key = json.load(f)['wgApi']

WOT_BASE_URL: str = "https://api.worldoftanks.eu/wot"


class NotAuthenticatedException(Exception):
    pass


class WrongUsernameException(Exception):
    def __init__(self, name: str) -> None:
        self.name = name


class WrongPasswordException(Exception):
    def __init__(self, name: str) -> None:
        self.name = name


class PlayerNotFoundException(Exception):
    def __init__(self, name: str) -> None:
        self.name = name


class WgApiException(Exception):
    def __init__(self, name: str) -> None:
        self.name = name


class WgApiMissingDataException(Exception):
    def __init__(self, name: str) -> None:
        self.name = name


login_manager = LoginManager(
    SECRET, token_url="/login", use_cookie=True, cookie_name="cookie-name", not_authenticated_exception=NotAuthenticatedException
)


@app.exception_handler(NotAuthenticatedException)
async def auth_exception_handler(request: Request, exc: NotAuthenticatedException):
    return templates.TemplateResponse("login_error.html", {"request": request, "error": "You have to sign in first."})


@app.exception_handler(WrongUsernameException)
async def wrong_username_handler(request: Request, exc: WrongUsernameException):
    return templates.TemplateResponse("login_error.html", {"request": request, "error": str(exc)})


@app.exception_handler(WrongPasswordException)
async def wrong_password_handler(request: Request, exc: WrongPasswordException):
    return templates.TemplateResponse("login_error.html", {"request": request, "error": str(exc)})


@app.exception_handler(PlayerNotFoundException)
async def player_not_found_handler(request: Request, exc: PlayerNotFoundException):
    return templates.TemplateResponse("error.html", {"request": request, "error": str(exc)})


@app.exception_handler(httpx.ConnectError)
async def connection_error(request: Request, exc: httpx.ConnectError):
    message: str = "Connection error - could not connect to the server."
    return templates.TemplateResponse("error.html", {"request": request, "error": message})


@app.exception_handler(httpx.ConnectTimeout)
async def connection_timeout(request: Request, exc: httpx.ConnectTimeout):
    message: str = "Connection timeout - exceeded connection to the server time limit."
    return templates.TemplateResponse("error.html", {"request": request, "message": message})


@app.exception_handler(WgApiException)
async def wg_api_exception(request: Request, exc: WgApiException):
    return templates.TemplateResponse("error.html", {"request": request, "error": str(exc)})


@app.exception_handler(WgApiMissingDataException)
async def wg_missing_data(request: Request, exc: WgApiMissingDataException):
    return templates.TemplateResponse("error.html", {"request": request, "error": str(exc)})


@login_manager.user_loader()
def load_user(username: str):
    user = DB.get(username)
    return user


@app.get("/", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request, data: OAuth2PasswordRequestForm = Depends()):
    username = data.username
    password = data.password
    user = load_user(username)
    if not user:
        raise WrongUsernameException("Wrong username.")
    elif password != user["password"]:
        raise WrongPasswordException("Wrong password.")

    access_token = login_manager.create_access_token(data={"sub": username})
    response = RedirectResponse(url="/main/", status_code=302)
    login_manager.set_cookie(response, access_token)
    return response


@app.get("/main/", response_class=HTMLResponse)
async def root(request: Request, _=Depends(login_manager)):
    random_fact = "Here will be your random fact."
    return templates.TemplateResponse("index.html", {"request": request, "random_fact": random_fact})


@app.post("/main/", response_class=HTMLResponse)
async def root_fact(request: Request, _=Depends(login_manager)):
    fact_url = "https://uselessfacts.jsph.pl/api/v2/facts/random"
    async with httpx.AsyncClient() as client:
        fact_response = await client.get(url=fact_url)

    random_fact = fact_response.json()["text"]
    return templates.TemplateResponse("index.html", {"request": request, "random_fact": random_fact})


@app.post("/main/player/", response_class=HTMLResponse)
async def player_statistics(nickname: Annotated[str, Form()], request: Request, _=Depends(login_manager)):
    id_url: str = f"{WOT_BASE_URL}/account/list/?application_id={wot_api_key}&search={nickname}"
    async with httpx.AsyncClient() as client:
        id_response = await client.get(url=id_url)

    data = id_response.json()
    if data["status"] != "ok":
        raise WgApiException(data["error"]["message"])

    data = data["data"]
    if len(data) < 1:
        raise PlayerNotFoundException("Player with such nickname not found: " + nickname)

    try:
        player_id: int = player_id_service(data, nickname)
    except KeyError:
        raise WgApiMissingDataException("Some data missing in WG database.")

    if player_id == -1:
        raise PlayerNotFoundException("Player with such nickname not found: " + nickname)

    data_url: str = f"{WOT_BASE_URL}/account/info/?application_id={wot_api_key}&account_id={player_id}"
    async with httpx.AsyncClient() as client:
        player_response = await client.get(url=data_url)

    player_data = player_response.json()
    if player_data["status"] != "ok":
        raise WgApiException(player_data["error"]["message"])

    try:
        player_data: Player = player_stats_service(player_data["data"][str(player_id)])
    except KeyError:
        raise WgApiMissingDataException("Some data missing in WG database.")
    return templates.TemplateResponse("player_stats.html", {"request": request, "player_data": player_data})


@app.post("/main/tanks_list/", response_class=HTMLResponse)
async def tanks_list(
        nation: Annotated[str, Form()],
        tier: Annotated[str, Form()],
        tank_type: Annotated[str, Form()],
        request: Request,
        _=Depends(login_manager)
):
    url = f"{WOT_BASE_URL}/encyclopedia/vehicles/?application_id={wot_api_key}"

    if nation != "none":
        url += f"&nation={nation}"
    if tier != "none":
        url += f"&tier={tier}"
    if tank_type != "none":
        url += f"&type={tank_type}"

    async with httpx.AsyncClient() as client:
        tank_list_response = await client.get(url=url)

    tanks_list_data = tank_list_response.json()
    if tanks_list_data["status"] != "ok":
        raise WgApiException(tanks_list_data["error"]["message"])

    tanks_list_data: dict = tanks_list_data["data"]
    try:
        tanks: list[Tank] = tanks_list_service(tanks_list_data)
    except KeyError:
        raise WgApiMissingDataException("Some data missing in WG database.")

    return templates.TemplateResponse("tanks_list.html", {"request": request, "tanks": tanks})


@app.post("/main/tanks_list/{tank_id}", response_class=HTMLResponse)
async def tank_details(
        tank_id: int,
        tank_name: Annotated[str, Form()],
        tank_type: Annotated[str, Form()],
        nation: Annotated[str, Form()],
        tier: Annotated[int, Form()],
        tank_img_url: Annotated[str, Form()],
        description: Annotated[str, Form()],
        request: Request,
        _=Depends(login_manager)
):
    url: str = f"{WOT_BASE_URL}/encyclopedia/vehicleprofile/?application_id={wot_api_key}&tank_id={tank_id}"
    async with httpx.AsyncClient() as client:
        tank_details_response = await client.get(url=url)

    tank_details_data = tank_details_response.json()
    if tank_details_data["status"] != "ok":
        raise WgApiException(tank_details_data["error"]["message"])

    try:
        tank_details_data: dict = tank_details_data["data"][str(tank_id)]
        tank: TankDetails = tank_details_service(
            tank_details_data, tank_name, tank_type, nation, tier, tank_img_url, description
        )
    except KeyError:
        raise WgApiMissingDataException("Some data missing in WG database.")

    return templates.TemplateResponse("tank_details.html", {"request": request, "tank": tank})


if __name__ == "__main__":
    uvicorn.run("main:app", port=8080, log_level="info", reload=True)
