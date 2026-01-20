from sqlalchemy.dialects.postgresql.base import PGDialect
import re

old_initialize = PGDialect.initialize

def patched_initialize(self, connection):
    try:
        old_initialize(self, connection)
    except AssertionError:
        version_string = connection.exec_driver_sql("SELECT version()").scalar()
        match = re.search(r"v?(\d+\.\d+)", version_string)
        if match:
            self.server_version_info = tuple(map(int, match.group(1).split(".")))
        else:
            self.server_version_info = (25, 0)  # fallback

PGDialect.initialize = patched_initialize

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()
cors = CORS()
bcrypt = Bcrypt()
# limiter = Limiter(key_func=get_remote_address, default_limits=["600 per hour"])
