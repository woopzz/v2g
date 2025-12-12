import logging
import os
import shutil

import uvicorn

from v2g.core.config import DEFAULT_PROMETHEUS_MULTIPROC_DIR, settings

logger = logging.getLogger(__name__)


def setup_prometheus_multiproc_dir():
    """
    Reason: https://prometheus.github.io/client_python/multiprocess/

    Note that we don't call prometheus_client.multiprocess.mark_process_dead(dead_worker_pid).
    It does nothing since we don't collect metrics of the gauge type.
    """
    env_var_name = 'PROMETHEUS_MULTIPROC_DIR'

    path = os.getenv(env_var_name)
    if not path:
        path = DEFAULT_PROMETHEUS_MULTIPROC_DIR
        os.environ[env_var_name] = path
        logger.info(
            'The %s directory will be used to store Prometheus metrics. Added to env vars.',
            path,
        )

    if os.path.isdir(path):
        shutil.rmtree(path)
        logger.info('The old %s directory was deleted.', path)

    dir_perm = 0o744
    os.mkdir(path, mode=dir_perm)
    logger.info('The new %s directory was created.', path)


if __name__ == '__main__':
    setup_prometheus_multiproc_dir()
    uvicorn.run(
        app='v2g.app:app',
        host=settings.uvicorn.host,
        port=settings.uvicorn.port,
        workers=settings.uvicorn.workers,
        reload=settings.uvicorn.reload,
    )
