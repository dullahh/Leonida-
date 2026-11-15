"""Single full-state transport projection; reads do not run the calculation again."""
from .runtime import Runtime
from .schemas import StreamEnvelope


class StateProjector:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime

    def snapshot(self, run_id: str | None = None) -> StreamEnvelope:
        return self.runtime.snapshot(run_id)
