from fastapi import FastAPI

from v2g.config import settings
from v2g.routers.conversion import router as router_conversion

app = FastAPI()
app.include_router(router_conversion, prefix='/conversion')

if __name__ == '__main__':
    import uvicorn
    import multiprocessing

    dev = settings.uvicorn.dev

    if dev:
        workers = 1
    else:
        workers = multiprocessing.cpu_count() * 2 + 1

    uvicorn.run(
        app='main:app',
        host=settings.uvicorn.host,
        port=settings.uvicorn.port,
        workers=workers,
        reload=dev,
    )
