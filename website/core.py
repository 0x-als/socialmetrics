from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

templates = Jinja2Templates(directory="website/templates")
templates.env.loader = ChoiceLoader([
    FileSystemLoader("website/templates/base"),
    FileSystemLoader("website/templates/dashboard"),
    FileSystemLoader("website/templates/social_network"),
    FileSystemLoader("website/templates/login"),
    FileSystemLoader("website/templates/settings"),
])