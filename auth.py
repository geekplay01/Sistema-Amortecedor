"""Login de administrador (um usuário local por enquanto; já preparado para mais perfis via coluna `role`).
  • Primeiro acesso: o app pede para CRIAR o administrador (nenhuma senha padrão).
  • Depois: login por sessão. Senha guardada com hash (werkzeug/scrypt), nunca em texto.
  • Desligar (só em desenvolvimento):  PSD_AUTH=off
  • Esqueceu a senha:  python auth.py reset   (apaga os usuários; no próximo acesso o app pede um novo administrador)
"""
import os, re, sys, time, secrets
from flask import request, session, redirect, url_for, render_template, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import database as db

OPEN_PREFIXES = ("/login", "/setup", "/logout", "/static/", "/vendor/", "/favicon.ico", "/api/auth/me")
_FAILS = {}      # ip -> [timestamps] (bloqueio simples contra tentativas em sequência)

def enabled(): return os.environ.get("PSD_AUTH", "on").lower() != "off"

def _ensure():
    c = db.conn()
    try:
        c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL COLLATE NOCASE, pw_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'admin', created_at TEXT DEFAULT CURRENT_TIMESTAMP, last_login TEXT)")
        if "avatar" not in {r[1] for r in c.execute("PRAGMA table_info(users)")}: c.execute("ALTER TABLE users ADD COLUMN avatar TEXT")
        c.commit()
    finally: c.close()

def n_users():
    _ensure(); c = db.conn()
    try: return c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally: c.close()

def secret_key():
    if os.environ.get("FLASK_SECRET"): return os.environ["FLASK_SECRET"]
    p = os.path.join(os.path.dirname(db.DB_PATH), ".secret_key"); os.makedirs(os.path.dirname(p), exist_ok=True)
    if not os.path.exists(p): open(p, "w").write(secrets.token_hex(32))
    return open(p).read().strip()

def create_user(username, password, role="admin"):
    username = (username or "").strip()
    if len(username) < 3: raise ValueError("O usuário precisa ter ao menos 3 caracteres.")
    if len(password or "") < 8: raise ValueError("A senha precisa ter ao menos 8 caracteres.")
    _ensure(); c = db.conn()
    try:
        c.execute("INSERT INTO users(username,pw_hash,role) VALUES(?,?,?)", (username, generate_password_hash(password), role)); c.commit()
    except Exception as e:
        if "UNIQUE" in str(e): raise ValueError("Esse usuário já existe.")
        raise
    finally: c.close()

def check(username, password):
    _ensure(); c = db.conn()
    try:
        r = c.execute("SELECT id,username,pw_hash,role,avatar FROM users WHERE username=?", ((username or "").strip(),)).fetchone()
        if r and check_password_hash(r["pw_hash"], password or ""):
            c.execute("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?", (r["id"],)); c.commit(); return {"id": r["id"], "username": r["username"], "role": r["role"], "avatar": bool(r["avatar"])}
    finally: c.close()
    return None

def change_password(username, old, new):
    if not check(username, old): raise ValueError("Senha atual incorreta.")
    if len(new or "") < 8: raise ValueError("A nova senha precisa ter ao menos 8 caracteres.")
    c = db.conn()
    try: c.execute("UPDATE users SET pw_hash=? WHERE username=?", (generate_password_hash(new), username)); c.commit()
    finally: c.close()

def _row(uid):
    _ensure(); c = db.conn()
    try: return c.execute("SELECT id,username,role,avatar,created_at,last_login FROM users WHERE id=?", (uid,)).fetchone()
    finally: c.close()

def current_user():
    u = session.get("user")
    if not u: return None
    r = _row(u["id"])          # sempre o estado atual (usuário renomeado, perfil alterado, conta removida)
    if not r: session.clear(); return None
    return {"id": r["id"], "username": r["username"], "role": r["role"], "avatar": bool(r["avatar"])}

AVATAR_DIR = os.path.join(db.BASE, "data", "avatars")

def change_username(uid, password, new):
    new = (new or "").strip()
    if len(new) < 3: raise ValueError("O usuário precisa ter ao menos 3 caracteres.")
    if not re.fullmatch(r"[\w.\-@]+", new): raise ValueError("Use apenas letras, números, ponto, hífen, sublinhado ou @.")
    r = _row(uid)
    if not r or not check(r["username"], password): raise ValueError("Senha atual incorreta.")
    c = db.conn()
    try: c.execute("UPDATE users SET username=? WHERE id=?", (new, uid)); c.commit()
    except Exception as e:
        if "UNIQUE" in str(e): raise ValueError("Esse usuário já existe.")
        raise
    finally: c.close()

def set_avatar(uid, data):
    """Foto de perfil: aceita PNG/JPG/WEBP/GIF, recorta quadrado e grava 256×256 PNG (remove metadados)."""
    from PIL import Image
    import io
    if len(data) > 8 * 1024 * 1024: raise ValueError("A foto precisa ter até 8 MB.")
    try: im = Image.open(io.BytesIO(data)); im.load()
    except Exception: raise ValueError("Arquivo não é uma imagem válida (use PNG, JPG ou WEBP).")
    im = im.convert("RGBA"); w, h = im.size; s = min(w, h); im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((256, 256), Image.LANCZOS)
    os.makedirs(AVATAR_DIR, exist_ok=True); im.save(os.path.join(AVATAR_DIR, f"{int(uid)}.png"), "PNG")
    c = db.conn()
    try: c.execute("UPDATE users SET avatar=? WHERE id=?", (f"{int(uid)}.png", uid)); c.commit()
    finally: c.close()

def clear_avatar(uid):
    p = os.path.join(AVATAR_DIR, f"{int(uid)}.png")
    if os.path.exists(p): os.remove(p)
    c = db.conn()
    try: c.execute("UPDATE users SET avatar=NULL WHERE id=?", (uid,)); c.commit()
    finally: c.close()

# ---- administração de usuários ----
def list_users():
    _ensure(); c = db.conn()
    try: return [dict(r) | {"avatar": bool(r["avatar"])} for r in c.execute("SELECT id,username,role,avatar,created_at,last_login FROM users ORDER BY username")]
    finally: c.close()

def _admins():
    c = db.conn()
    try: return c.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
    finally: c.close()

def admin_set_role(uid, role):
    if role not in ("admin", "user"): raise ValueError("Perfil inválido.")
    r = _row(uid)
    if not r: raise ValueError("Usuário não encontrado.")
    if r["role"] == "admin" and role != "admin" and _admins() <= 1: raise ValueError("Precisa existir ao menos um administrador.")
    c = db.conn()
    try: c.execute("UPDATE users SET role=? WHERE id=?", (role, uid)); c.commit()
    finally: c.close()

def admin_reset_password(uid, new):
    if len(new or "") < 8: raise ValueError("A nova senha precisa ter ao menos 8 caracteres.")
    if not _row(uid): raise ValueError("Usuário não encontrado.")
    c = db.conn()
    try: c.execute("UPDATE users SET pw_hash=? WHERE id=?", (generate_password_hash(new), uid)); c.commit()
    finally: c.close()

def admin_delete(uid, by_id):
    r = _row(uid)
    if not r: raise ValueError("Usuário não encontrado.")
    if uid == by_id: raise ValueError("Você não pode remover a si mesmo.")
    if r["role"] == "admin" and _admins() <= 1: raise ValueError("Precisa existir ao menos um administrador.")
    clear_avatar(uid); c = db.conn()
    try: c.execute("DELETE FROM users WHERE id=?", (uid,)); c.commit()
    finally: c.close()
def is_admin(): return (current_user() or {}).get("role") == "admin" or not enabled()

def _blocked(ip):
    t = time.time(); _FAILS[ip] = [x for x in _FAILS.get(ip, []) if t - x < 600]; return len(_FAILS[ip]) >= 5

def init_app(app):
    app.secret_key = secret_key(); app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=60 * 60 * 12)

    @app.before_request
    def gate():
        if not enabled() or request.path.startswith(OPEN_PREFIXES): return None
        if n_users() == 0: return (jsonify(error="Crie o administrador em /setup.", setup=True), 401) if request.path.startswith("/api/") else redirect(url_for("setup"))
        if current_user(): return None
        return (jsonify(error="Faça login.", login=True), 401) if request.path.startswith("/api/") else redirect(url_for("login", next=request.full_path.rstrip("?")))

    def _safe_next(n): return n if n and n.startswith("/") and not n.startswith("//") else "/"

    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        if n_users() > 0: return redirect(url_for("login"))
        err = None
        if request.method == "POST":
            f = request.form
            try:
                if f.get("password") != f.get("password2"): raise ValueError("As senhas não conferem.")
                create_user(f.get("username"), f.get("password"), "admin"); u = check(f.get("username"), f.get("password")); session.clear(); session["user"] = u; session.permanent = True; return redirect("/")
            except ValueError as e: err = str(e)
        return render_template("login.html", mode="setup", error=err, next="/")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if enabled() and n_users() == 0: return redirect(url_for("setup"))
        err = None; nxt = _safe_next(request.values.get("next"))
        if request.method == "POST":
            ip = request.remote_addr or "?"
            if _blocked(ip): err = "Muitas tentativas. Aguarde alguns minutos."
            else:
                u = check(request.form.get("username"), request.form.get("password"))
                if u: _FAILS.pop(ip, None); session.clear(); session["user"] = u; session.permanent = True; return redirect(nxt)
                _FAILS.setdefault(ip, []).append(time.time()); err = "Usuário ou senha incorretos."
        return render_template("login.html", mode="login", error=err, next=nxt)

    @app.route("/logout")
    def logout(): session.clear(); return redirect(url_for("login"))

    @app.get("/api/auth/me")
    def me():
        u = current_user(); r = _row(u["id"]) if u else None
        return jsonify(user=(dict(u) | {"created_at": r["created_at"], "last_login": r["last_login"]}) if u else None, auth=enabled(), admin=is_admin())

    def _need_user():
        u = current_user()
        if not u: raise PermissionError("Faça login.")
        return u
    def _need_admin():
        if not is_admin(): raise PermissionError("Somente administradores.")
        return current_user()
    @app.errorhandler(PermissionError)
    def _denied(e): return jsonify(error=str(e)), 403

    @app.post("/api/auth/username")
    def uname():
        b = request.get_json(force=True) or {}; u = _need_user()
        try: change_username(u["id"], b.get("password"), b.get("username"))
        except ValueError as e: return jsonify(error=str(e)), 400
        return jsonify(ok=True, username=(b.get("username") or "").strip())

    @app.post("/api/auth/avatar")
    def avatar_up():
        u = _need_user(); f = request.files.get("file")
        if not f: return jsonify(error="Escolha uma imagem."), 400
        try: set_avatar(u["id"], f.read())
        except ValueError as e: return jsonify(error=str(e)), 400
        return jsonify(ok=True)

    @app.delete("/api/auth/avatar")
    def avatar_del(): clear_avatar(_need_user()["id"]); return jsonify(ok=True)

    @app.get("/avatar/<int:uid>")
    def avatar_get(uid):
        from flask import send_file, abort
        _need_user(); r = _row(uid); p = os.path.join(AVATAR_DIR, f"{uid}.png")
        if not r or not r["avatar"] or not os.path.exists(p): abort(404)
        resp = send_file(p, mimetype="image/png"); resp.headers["Cache-Control"] = "private, max-age=60"; return resp

    @app.get("/api/admin/users")
    def adm_users(): _need_admin(); return jsonify(users=list_users(), me=(current_user() or {}).get("id"))

    @app.post("/api/admin/users")
    def adm_user_new():
        _need_admin(); b = request.get_json(force=True) or {}
        try: create_user(b.get("username"), b.get("password"), b.get("role") if b.get("role") in ("admin", "user") else "user")
        except ValueError as e: return jsonify(error=str(e)), 400
        return jsonify(ok=True)

    @app.put("/api/admin/users/<int:uid>")
    def adm_user_set(uid):
        _need_admin(); b = request.get_json(force=True) or {}
        try:
            if b.get("role"): admin_set_role(uid, b["role"])
            if b.get("password"): admin_reset_password(uid, b["password"])
        except ValueError as e: return jsonify(error=str(e)), 400
        return jsonify(ok=True)

    @app.delete("/api/admin/users/<int:uid>")
    def adm_user_del(uid):
        me_ = _need_admin()
        try: admin_delete(uid, (me_ or {}).get("id"))
        except ValueError as e: return jsonify(error=str(e)), 400
        return jsonify(ok=True)

    @app.post("/api/auth/password")
    def pw():
        b = request.get_json(force=True) or {}; u = current_user()
        if not u: return jsonify(error="Faça login."), 401
        try: change_password(u["username"], b.get("old"), b.get("new"))
        except ValueError as e: return jsonify(error=str(e)), 400
        return jsonify(ok=True)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        if input("Apagar TODOS os usuários? (digite SIM) ").strip() == "SIM":
            _ensure(); c = db.conn(); c.execute("DELETE FROM users"); c.commit(); c.close(); print("Pronto. No próximo acesso o app pede a criação do administrador.")
    else: print("uso: python auth.py reset")
