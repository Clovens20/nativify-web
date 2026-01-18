import asyncio
import os
import sys


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


# Maintenant démarrer uvicorn
if __name__ == "__main__":
    import uvicorn

    default_port = "8000" if os.environ.get("ENVIRONMENT") == "development" else "10000"
    port = int(os.environ.get("PORT", default_port))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.environ.get("ENVIRONMENT") == "development",
        app_dir=".",
    )

