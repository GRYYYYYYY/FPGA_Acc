"""Exact scalar CachedBoundRC formula, independent of graph object storage.

Caller must validate node cost-index provenance and full physical arc coverage.
Zero initial upstream state matches the existing additive baseline, not tree STA.
"""
from fractions import Fraction
import xml.etree.ElementTree as ET
from path_rc import number

class StreamingCachedArcCost:
    def __init__(self, switches, bases, normalization, scale=10**6):
        if type(scale) is not int or scale < 1:
            raise ValueError('invalid scale')
        self.scale = scale
        self.normalization = number(normalization)
        if not self.normalization:
            raise ValueError('invalid normalization')
        self.bases = {}
        for index, value in bases.items():
            if type(index) is not int or index < 0:
                raise ValueError('invalid cost index')
            self.bases[index] = number(value)
        self.switches = {}
        for sid, xml in switches.items():
            if type(sid) is not int or sid < 0:
                raise ValueError('invalid switch ID')
            element = ET.fromstring(xml)
            if element.get('type') not in {'mux', 'tristate', 'buffer'}:
                raise ValueError('nonbuffered graph requires resistance state')
            timing = element.find('timing')
            if timing is None:
                raise ValueError('missing switch timing element')
            self.switches[sid] = tuple(number(timing.get(k, '0'))
                                       for k in ('R', 'Tdel', 'Cinternal'))
        self.cache = {}
        self.queries = 0

    def cost(self, switch_id, source_r, destination_r, destination_c,
             cost_index, destination_capacity=1):
        if type(switch_id) is not int or switch_id not in self.switches:
            raise ValueError('invalid switch ID')
        if type(cost_index) is not int or cost_index not in self.bases:
            raise ValueError('invalid cost index')
        if type(destination_capacity) is not int or destination_capacity < 0:
            raise ValueError('invalid destination capacity')
        source_r, r, c = map(number, (source_r, destination_r, destination_c))
        key = (switch_id, source_r, r, c, cost_index)
        self.queries += 1
        if key not in self.cache:
            sr, intrinsic, internal = self.switches[switch_id]
            new_r = sr + r
            delay = intrinsic + (new_r-r/2)*c + (new_r-source_r/2)*internal
            if delay < 0:
                raise ValueError('negative RC increment')
            value = round((delay+self.bases[cost_index]) /
                          self.normalization*self.scale/2)
            self.cache[key] = value
        # Validate even disabled arcs, matching CachedBoundRC.
        return self.cache[key] if destination_capacity else None
