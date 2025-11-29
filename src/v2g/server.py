import uvicorn

from v2g.core.config import settings

if __name__ == '__main__':
    uvicorn.run(
        app='v2g.app:app',
        host=settings.uvicorn.host,
        port=settings.uvicorn.port,
        workers=settings.uvicorn.workers,
        reload=settings.uvicorn.reload,
    )
