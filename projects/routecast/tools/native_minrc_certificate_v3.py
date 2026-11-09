"""Consistent capacity preconditions for native and arbitrary-integer minRC APIs."""
from collections import Counter
from native_minrc_certificate_v2 import NativeMinRCCertificate as _V2, MAX, nonnegative_integer


class NativeMinRCCertificate(_V2):
    def _capacity_constraints(self, source, outside):
        self._validate_source(source)
        result = Counter()
        for node, count in outside.items():
            if type(node) is not int or not 0 <= node < self.n:
                raise ValueError('Occupancy node outside immutable graph')
            if not nonnegative_integer(count):
                raise ValueError('Occupancy requires nonnegative integer counts')
            # Eligibility only tests count < capacity; saturation is exact for
            # this predicate and avoids truncation of arbitrary-size counts.
            result[node] = min(count, self.f['capacities'][node])
        if result[source] >= self.f['capacities'][source]:
            raise ValueError('minRC source is blocked by capacity')
        return result

    def query(self, source, sink, budget, outside, kept, parents, max_labels,
              cost_limit_exclusive):
        outside = self._capacity_constraints(source, outside)
        return super().query(source, sink, budget, outside, kept, parents,
                             max_labels, cost_limit_exclusive)

    def query_with_certificate(self, source, sink, budget, outside, parents,
                               max_labels):
        outside = self._capacity_constraints(source, outside)
        return super().query_with_certificate(source, sink, budget, outside,
                                              parents, max_labels)
