"""Serial model-only trial gate; never publishes routing or certifies native STA."""
from fractions import Fraction
from exact_incremental_timing_dag import ExactTimingDAG


def exact_nonnegative(value):
    if isinstance(value, (bool, float)):
        raise ValueError('exact rational required')
    value = Fraction(value)
    if value < 0:
        raise ValueError('negative model value')
    return value


class LiveStateDAGScreen:
    def __init__(self, nodes, edges, sinks, published_delays_ns, published_wirelength):
        self._delays = self._vector(published_delays_ns)
        self._wire = self._wire_value(published_wirelength)
        self._dag = ExactTimingDAG(nodes, edges, sinks, self._delays)
        self._cpd = self._dag.cpd

    @staticmethod
    def _vector(values):
        result = {}
        for key, value in values.items():
            key = str(key)
            if key in result:
                raise ValueError('duplicate normalized connection ID')
            result[key] = exact_nonnegative(value)
        if not result:
            raise ValueError('empty delay vector')
        return result

    @staticmethod
    def _wire_value(value):
        if type(value) is not int or value < 0:
            raise ValueError('nonnegative integer wirelength required')
        return value

    def trial(self, delays_ns, wirelength, *, complete):
        if type(complete) is not bool:
            raise ValueError('explicit completion flag required')
        if not complete:
            return dict(model_admitted=False, reasons=['INCOMPLETE_MODEL'])
        delays = self._vector(delays_ns)
        if delays.keys() != self._delays.keys():
            raise ValueError('candidate must contain every published connection ID')
        wire = self._wire_value(wirelength)
        cpd = self._dag.update({k:v for k,v in delays.items() if v != self._delays[k]})
        reasons = []
        if wire > self._wire:
            reasons.append('MODEL_WIRE_REGRESSION')
        if cpd > self._cpd:
            reasons.append('MODEL_DAG_TIMING_REGRESSION')
        return dict(model_admitted=not reasons, reasons=reasons,
                    published_model_cpd_ns=str(self._cpd), candidate_model_cpd_ns=str(cpd),
                    published_wirelength=self._wire, candidate_wirelength=wire,
                    scope='Model decision only; native FULL/STA still required. Serial trial, no publication.')
