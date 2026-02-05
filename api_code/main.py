from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi import status
from database import get_db
from auth import require_admin
from minio_service import init_minio, upload_file, list_files

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret123")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

init_minio()

# ================= LOGIN =================
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request,
          username: str = Form(...),
          password: str = Form(...)):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT role FROM users WHERE username=%s AND password=%s",
        (username, password)
    )
    user = cur.fetchone()
    cur.close()
    db.close()

    if not user:
        return RedirectResponse("/", status_code=302)

    request.session["user"] = username
    request.session["role"] = user[0]

    if user[0] == "admin":
        return RedirectResponse("/admin", status_code=302)
    return RedirectResponse("/user", status_code=302)

# Log out
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

# ================= DASHBOARD =================
@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    bucket: str = "document",
    folder: str = "tin10"
):
    check = require_admin(request)
    if check:
        return check

    files = list_files(bucket, folder)

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "files": files,
            "bucket": bucket,
            "folder": folder
        }
    )


# ================= USER MANAGEMENT =================
@app.get("/admin/users", response_class=HTMLResponse)
def admin_users(request: Request):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, username, role FROM users")
    users = cur.fetchall()
    cur.close()
    db.close()
    return templates.TemplateResponse(
        "admin_users.html",
        {"request": request, "users": users}
    )

@app.post("/admin/users/add")
def add_user(username: str = Form(...),
             password: str = Form(...),
             role: str = Form(...)):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO users(username,password,role) VALUES(%s,%s,%s)",
        (username, password, role)
    )
    db.commit()
    cur.close()
    db.close()
    return RedirectResponse("/admin/users", status_code=302)

@app.get("/admin/users/edit/{user_id}", response_class=HTMLResponse)
def edit_user_form(request: Request, user_id: int):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, username, role FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    db.close()
    return templates.TemplateResponse(
        "admin_user_edit.html",
        {"request": request, "user": user}
    )

@app.post("/admin/users/edit")
def edit_user(user_id: int = Form(...),
              username: str = Form(...),
              password: str = Form(...),
              role: str = Form(...)):
    db = get_db()
    cur = db.cursor()

    if password.strip():
        cur.execute(
            "UPDATE users SET username=%s,password=%s,role=%s WHERE id=%s",
            (username, password, role, user_id)
        )
    else:
        cur.execute(
            "UPDATE users SET username=%s,role=%s WHERE id=%s",
            (username, role, user_id)
        )

    db.commit()
    cur.close()
    db.close()
    return RedirectResponse("/admin/users", status_code=302)

@app.post("/admin/users/delete")
def delete_user(user_id: int = Form(...)):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    db.commit()
    cur.close()
    db.close()
    return RedirectResponse("/admin/users", status_code=302)

# ================= MINIO =================
@app.post("/admin/upload")
def upload(
    request: Request,
    bucket: str = Form(...),
    folder: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        upload_file(bucket, folder, file)
        request.session["upload_msg"] = "✅ Upload thành công!"
        request.session["upload_status"] = "success"
    except Exception as e:
        request.session["upload_msg"] = f"❌ Upload thất bại: {str(e)}"
        request.session["upload_status"] = "danger"

    return RedirectResponse("/admin", status_code=302)

@app.get("/admin/storage", response_class=HTMLResponse)
def storage(request: Request,
            bucket: str = "document",
            folder: str = "tin10"):
    files = list_files(bucket, folder)
    return templates.TemplateResponse(
        "admin_storage.html",
        {
            "request": request,
            "bucket": bucket,
            "folder": folder,
            "files": files
        }
    )


@app.get("/user", response_class=HTMLResponse)
def user_dashboard(request: Request,
                   bucket: str = "document",
                   folder: str = "tin10",
                   keyword: str = ""):
    from auth import require_user
    check = require_user(request)
    if check:
        return check

    files = list_files(bucket, folder)

    if keyword:
        files = [f for f in files if keyword.lower() in f.lower()]

    return templates.TemplateResponse(
        "user_dashboard.html",
        {
            "request": request,
            "files": files,
            "bucket": bucket,
            "folder": folder,
            "keyword": keyword
        }
    )
