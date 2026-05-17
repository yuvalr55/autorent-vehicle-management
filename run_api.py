from dotenv import load_dotenv
import os
import uvicorn

load_dotenv()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.environ["API_HOST"],
        port=int(os.environ["API_PORT"]),
        log_level=os.environ["LOG_LEVEL"].lower(),
    )
