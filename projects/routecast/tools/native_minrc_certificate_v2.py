"""Explicit nonnegative integer model contract around the frozen exact minRC kernel.

The RC graph/increments are immutable for the lifetime of the context. Large
nonnegative integers retain the v1 exact Python fallback, without quantization.
"""
from native_minrc_certificate_v1 import NativeMinRCCertificate as _V1, MAX


def nonnegative_integer(value):
    return type(value) is int and value >= 0


class NativeMinRCCertificate(_V1):
    def __init__(self, rc):
        if not all(nonnegative_integer(v) for v in rc.increments):
            raise ValueError('minRC requires nonnegative integer increments')
        super().__init__(rc)

    def _validate_source(self, source):
        self.rc.node(source)
        if not nonnegative_integer(self.rc.initial(source)):
            raise ValueError('minRC requires nonnegative integer source delay')

    def query(self, source, sink, budget, outside, kept, parents, max_labels,
              cost_limit_exclusive):
        self._validate_source(source)
        return super().query(source, sink, budget, outside, kept, parents,
                             max_labels, cost_limit_exclusive)

    def query_with_certificate(self, source, sink, budget, outside, parents,
                               max_labels):
        self._validate_source(source)
        if outside[source] >= self.f['capacities'][source]:
            raise ValueError('minRC source is blocked by capacity')
        return super().query_with_certificate(source, sink, budget, outside,
                                              parents, max_labels)
