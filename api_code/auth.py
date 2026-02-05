from fastapi import Request
from fastapi.responses import RedirectResponse

def require_login(request: Request):
    if "user" not in request.session:
        return RedirectResponse("/", status_code=302)

def require_admin(request: Request):
    if request.session.get("role") != "admin":
        return RedirectResponse("/", status_code=302)

def require_user(request):
    if request.session.get("role") != "user":
        return RedirectResponse("/", status_code=302)
