import os
from config import base_dir
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from website.middleware.middleware import middleware
from website.routes.social_network import social_network
from website.routes.dashboard import dashboard
from website.routes.login import login
from website.routes.logout import logout
from website.routes.settings import scrape_accounts, settings, telegram_bots, proxies
from website.routes.users import users

app = FastAPI()
static_dir = os.path.join(base_dir / "website", "static")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(login.route)
app.include_router(dashboard.route)
app.include_router(logout.route)
app.include_router(settings.route)
app.include_router(scrape_accounts.route)
app.include_router(telegram_bots.route)
app.include_router(social_network.route)
app.include_router(proxies.route)
app.include_router(users.route)
app.middleware("http")(middleware)
