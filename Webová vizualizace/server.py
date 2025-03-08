import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.log
from urllib.request import urlopen
import datetime as dt
import logging
import sqlite3
import json
import bcrypt
import ssl
import os
from recognize_handler import RecognizeImageHandler


# Inicializace databáze
DB_FILE = "users.db"
tornado.log.enable_pretty_logging()
app_log = logging.getLogger("tornado.application")

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        conn.commit()

# Chráněný StaticFileHandler
class ProtectedStaticFileHandler(tornado.web.StaticFileHandler):
    def get_current_user(self):
        user = self.get_secure_cookie("user") or self.get_secure_cookie("faceid_auth")
        app_log.info(f"ProtectedStaticFileHandler: current_user={user}")
        return user

    def validate_absolute_path(self, root, absolute_path):
        if self.request.uri == "/index.html" and not self.get_current_user():
            app_log.warning("Access denied: Redirecting to login.html")
            self.redirect("/login.html")
            return None
        return super().validate_absolute_path(root, absolute_path)

# Handler pro přihlášení přes FaceID
class FaceIdLoginHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        face_id_verified = data.get("face_id_verified", False)
        username = data.get("username", None)

        if face_id_verified and username:
            app_log.info(f"FaceID login successful: username={username}")
            # Nastavení cookie pro FaceID přihlášení
            self.set_secure_cookie("faceid_auth", username, httponly=True, secure=True, expires_days=0.041)
            self.write({"success": True, "message": "FaceID login successful."})
        else:
            app_log.warning("FaceID login failed: Verification failed")
            self.write({"success": False, "message": "FaceID verification failed."})

# Handler pro chráněné stránky
class ProtectedPageHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user = self.get_secure_cookie("user") or self.get_secure_cookie("faceid_auth")
        app_log.info(f"ProtectedPageHandler: current_user={user}")
        return user

    def get(self):
        if not self.current_user:
            app_log.warning("Access denied: Redirecting to login.html")
            self.redirect("/login.html")
        else:
            app_log.info("Access granted: Rendering index.html")
            self.render("index.html")

# Handler pro registraci
class RegisterHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            self.write({'success': False, 'message': 'Username and password are required.'})
            return

        # Hashování hesla pomocí bcrypt
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        try:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
                conn.commit()
            self.write({'success': True, 'message': 'User registered successfully.'})
        except sqlite3.IntegrityError:
            self.write({'success': False, 'message': 'Username already exists.'})


# Handler pro odhlášení
class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/index1.html")

# Handler pro přihlášení
class LoginHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            self.write({'success': False, 'message': 'Username and password are required.'})
            return

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()

            if row and bcrypt.checkpw(password.encode(), row[0].encode()):
                # Nastavení zabezpečené cookie
                self.set_secure_cookie("user", username, httponly=True, secure=True)
                self.write({'success': True, 'message': 'Login successful.'})
            else:
                self.write({'success': False, 'message': 'Invalid username or password.'})


# Handlery pro různé cesty
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index1.html")

class TeamTemplateHandler(tornado.web.RequestHandler):
    def get(self):
        team = self.get_argument("team", "default")
        if team == "red":
            self.render("team_red.html", team=team)
        else:
            self.render("team_template.html", team=team)

class TeamDataHandler(tornado.web.RequestHandler):
    def get(self):
        team = self.get_argument("team", "default")
        data_type = self.get_argument("type", "default")
        
        if team == "red":
            if data_type == "temperature":
                self.render("temperature_red.html", team=team)
            elif data_type == "humidity":
                self.render("humidity_red.html", team=team)
            elif data_type == "illumination":
                self.render("illumination_red.html", team=team)
            else:
                self.write("Unknown data type for team Red")
        else:
            self.render("data_template.html", team=team, data_type=data_type)

class TemperatureTemplateHandler(tornado.web.RequestHandler):
    def get(self):
        team = self.get_argument("team", "default")
        if team == "red":
            self.render("temperature_red.html", team=team)
        else:
            self.render("temperature_template.html", team=team)

class HumidityTemplateHandler(tornado.web.RequestHandler):
    def get(self):
        team = self.get_argument("team", "default")
        if team == "red":
            self.render("humidity_red.html", team=team)
        else:
            self.render("humidity_template.html", team=team)

class IlluminationTemplateHandler(tornado.web.RequestHandler):
    def get(self):
        team = self.get_argument("team", "default")
        if team == "red":
            self.render("illumination_red.html", team=team)
        else:
            self.render("illumination_template.html", team=team)

class BonusTemperatureHandler(tornado.web.RequestHandler):
    def get(self):
        team = self.get_argument("team", "default")
        if team == "red":
            self.render("bonus_red.html", team=team)

class ReceiveImageHandler(tornado.web.RequestHandler):
    def post(self):
        # Convert from binary data to string
        received_data = self.request.body.decode()

        assert received_data.startswith("data:image/png"), "Only data:image/png URL supported"

        # Parse data:// URL
        with urlopen(received_data) as response:
            image_data = response.read()

        app_log.info("Received image: %d bytes", len(image_data))

        # Write an image to the file
        with open(f"images/img-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.png", "wb") as fw:
            fw.write(image_data)

# Funkce pro vytvoření Tornado aplikace
def make_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/team_template", TeamTemplateHandler),
            (r"/data_template", TeamDataHandler),
            (r"/temperature_template", TemperatureTemplateHandler),
            (r"/humidity_template", HumidityTemplateHandler),
            (r"/illumination_template", IlluminationTemplateHandler),
	    (r"/faceid_login", FaceIdLoginHandler),
	    (r"/register", RegisterHandler),
            (r"/login", LoginHandler),
	    (r"/logout", LogoutHandler),
	    (r"/receive_image", ReceiveImageHandler),
    	    (r"/recognize", RecognizeImageHandler),
            (r"/(.*)", ProtectedStaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "static")}),
        ],
	cookie_secret="YOUR_SECRET_KEY",
        template_path=os.path.join(os.path.dirname(__file__), "static"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        debug=True
    )

if __name__ == "__main__":
    init_db()

    app = make_app()

    # Nastavení SSL certifikátů
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(certfile="/etc/letsencrypt/live/sulis69.zcu.cz/fullchain.pem", 
                            keyfile="/etc/letsencrypt/live/sulis69.zcu.cz/privkey.pem")

    # Spuštění HTTPS serveru na portu 443
    https_server = tornado.httpserver.HTTPServer(app, ssl_options=ssl_ctx)
    https_server.listen(443)

    print("Server běží na https://<vaše_ip_adresa>")
    tornado.ioloop.IOLoop.current().start()
