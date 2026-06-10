from celery import Celery

from src.firebase.firebase import get_firebase_app
from src.config.main import Config

from celery.signals import worker_process_init

settings = Config() # type: ignore

celery_app = Celery(
    "push",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Amsterdam",
    enable_utc=True,
)
@worker_process_init.connect
def init_worker(**kwargs):
    get_firebase_app()

# Import all modules in `src.tasks` so task decorators execute and
# PromiseProxy objects are created/queued before finalization.
try:
    import pkgutil
    import importlib
    import sys
    try:
        import src.tasks as _tasks_pkg  # type: ignore
    except Exception:
        _tasks_pkg = None
    if _tasks_pkg is not None:
        for _finder, _name, _ispkg in pkgutil.walk_packages(_tasks_pkg.__path__, _tasks_pkg.__name__ + '.'):
            try:
                importlib.import_module(_name)
            except Exception as exc:  # pragma: no cover - warn but don't stop import chain
                print(f"Warning importing tasks module {_name!r}: {exc!r}", file=sys.stderr)
except Exception as exc:  # pragma: no cover - don't break imports on unexpected errors
    import sys
    print(f"Warning scanning/importing tasks package: {exc!r}", file=sys.stderr)

# Finalize the Celery app at import time to evaluate any pending
# lazy task decorators so PromiseProxy objects are resolved now.
try:
    celery_app.finalize()
    celery_app.autodiscover_tasks(['src.tasks.push']) 
except Exception as exc:  # pragma: no cover - don't break imports on finalize errors
    import sys
    print(f"Warning: celery_app.finalize() raised: {exc!r}", file=sys.stderr)