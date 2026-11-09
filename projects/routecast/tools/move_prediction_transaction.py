"""In-process whole-move snapshot publication; no external file/STA certification."""
from dataclasses import dataclass
from threading import RLock


@dataclass(frozen=True)
class MoveState:
    epoch: int
    context: str
    placement: bytes
    endpoints: bytes
    prediction: bytes
    budgets: bytes
    pressure: bytes
    search_cache: bytes = b''

    def __post_init__(self):
        if type(self.epoch) is not int or self.epoch < 0:
            raise ValueError('nonnegative epoch required')
        if not isinstance(self.context, str) or len(self.context) != 64 or any(c not in '0123456789abcdef' for c in self.context):
            raise ValueError('authenticated context digest required')
        for name in ('placement', 'endpoints', 'prediction', 'budgets', 'pressure', 'search_cache'):
            if type(getattr(self, name)) is not bytes:
                raise ValueError('immutable bytes payloads required')


class MovePredictionTransaction:
    def __init__(self, initial):
        if type(initial) is not MoveState:
            raise ValueError('MoveState required')
        self._current = initial
        self._lock = RLock()
        self._staging = False

    def snapshot(self):
        with self._lock:
            return self._current

    def commit(self, expected_epoch, build, validate):
        with self._lock:
            if self._staging:
                return 'BUSY'
            old = self._current
            if type(expected_epoch) is not int or old.epoch != expected_epoch:
                return 'STALE'
            self._staging = True
            try:
                candidate = build(old)
                if type(candidate) is not MoveState or candidate.epoch != old.epoch+1:
                    return 'INVALID_STATE'
                if candidate.context != old.context:
                    return 'CONTEXT_CHANGE'
                if validate(candidate) is not True:
                    return 'REJECTED'
            except Exception:
                return 'FAILED'
            finally:
                self._staging = False
            # A callback may reenter the transaction; never overwrite its newer state.
            if self._current is not old:
                return 'STALE'
            self._current = candidate
            return 'COMMITTED'
