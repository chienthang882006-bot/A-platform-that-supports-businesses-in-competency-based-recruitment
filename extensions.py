from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(get_remote_address)
talisman = Talisman()
