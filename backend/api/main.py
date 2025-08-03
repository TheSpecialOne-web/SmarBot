import os

import psutil
import uvicorn

num_cores = psutil.cpu_count(logical=False) or 1

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=600,
        workers=num_cores * 2 + 1,
        limit_max_requests=int(os.environ.get("UVICORN_MAX_REQUESTS", 500)),
    )
