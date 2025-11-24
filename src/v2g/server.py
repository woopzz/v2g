import uvicorn

from v2g.config import settings

if __name__ == '__main__':
    uvicorn.run(
        app='v2g.main:app',
        host=settings.uvicorn.host,
        port=settings.uvicorn.port,
        workers=settings.uvicorn.workers,
        reload=settings.uvicorn.reload,
    )
