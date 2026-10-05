import uvicorn

from dev.api.app import create_app
from dev.config import settings
from dev.logger import setup_logging

setup_logging()
app = create_app()

if __name__ == "__main__":
    host, port_str = settings.http_addr.split(":")
    port = int(port_str)

    # We must run with host "0.0.0.0" inside docker so it binds correctly,
    # but since settings.http_addr comes from env we just parse it.
    # The default ":8000" splits into host="" and port="8000".
    # uvicorn needs "0.0.0.0" if host is empty.
    host = host if host else "0.0.0.0"

    uvicorn.run("dev.main:app", host=host, port=port, log_config=None)
