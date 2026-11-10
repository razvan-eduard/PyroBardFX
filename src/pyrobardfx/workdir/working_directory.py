"""Places, guards and lays out the working directory."""

from dataclasses import dataclass
from pathlib import Path

from pyrobardfx.domain.constants import StageName
from pyrobardfx.events.constants import PERCENT_DONE
from pyrobardfx.events.fan_out import EventFanOut
from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.workdir.constants import (
    APP_FOLDER_NAME,
    DOCUMENTS_FOLDER_NAME,
    DOCUMENTS_PLATFORMS,
    EVENT_CREATED,
    EVENT_OPENED,
    HOME_OVERRIDE_ENV,
    LAYOUT,
    TEMP_ENV_VARS,
)
from pyrobardfx.workdir.host import HostFacts


@dataclass(frozen=True)
class WorkingDirectory:
    """The one folder that holds every story, sound, model and setting."""

    root: Path


class TempRoots:
    """The folders the host may empty on its own, so no working directory may live in them."""

    @staticmethod
    def of(host: HostFacts) -> tuple[Path, ...]:
        from_env = (host.environ.get(name, "") for name in TEMP_ENV_VARS)
        candidates = [host.system_temp, *(Path(value) for value in from_env if value)]
        candidates.extend(host.fixed_temp_roots)
        resolved = (path.resolve() for path in candidates if path.is_absolute())
        return tuple(dict.fromkeys(path for path in resolved if path.parent != path))

    @staticmethod
    def containing(host: HostFacts, path: Path) -> Path | None:
        target = path.resolve()
        return next((root for root in TempRoots.of(host) if TempRoots._holds(root, target)), None)

    @staticmethod
    def _holds(root: Path, target: Path) -> bool:
        """Tell whether `target` lies in `root`, also when the file system ignores letter case."""
        if target.is_relative_to(root):
            return True
        if not root.exists():
            return False
        existing = (folder for folder in (target, *target.parents) if folder.exists())
        return any(folder.samefile(root) for folder in existing)


class WorkingDirectoryService:
    """Opens the working directory for a start: picks its place, refuses bad ones, lays it out."""

    def __init__(self, host: HostFacts, events: EventFanOut) -> None:
        self._host = host
        self._events = events.at(StageName.WORKING_DIRECTORY_OPEN)

    def open(self, override: Path | None) -> WorkingDirectory:
        """Return the laid-out working directory or raise `RefusedError`."""
        root = self._chosen_root(override).absolute()
        temp_root = TempRoots.containing(self._host, root)
        if temp_root is not None:
            raise RefusedError(RefusalReason.IN_TEMP, root, str(temp_root))
        event = EVENT_OPENED if root.exists() else EVENT_CREATED
        self._lay_out(root)
        self._events.emit(event, PERCENT_DONE, path=str(root))
        return WorkingDirectory(root=root)

    @staticmethod
    def _lay_out(root: Path) -> None:
        try:
            for name in LAYOUT:
                (root / name).mkdir(parents=True, exist_ok=True)
        except OSError as error:
            detail = error.strerror or type(error).__name__
            raise RefusedError(RefusalReason.CANNOT_CREATE, root, detail) from error

    def _chosen_root(self, override: Path | None) -> Path:
        if override is not None:
            return override
        from_env = self._host.environ.get(HOME_OVERRIDE_ENV)
        if from_env:
            return Path(from_env)
        return self._default_root()

    def _default_root(self) -> Path:
        if self._host.platform in DOCUMENTS_PLATFORMS:
            return self._host.home / DOCUMENTS_FOLDER_NAME / APP_FOLDER_NAME
        return self._host.home / APP_FOLDER_NAME
