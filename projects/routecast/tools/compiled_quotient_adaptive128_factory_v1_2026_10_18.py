"""Independent adaptive128 candidate with unchanged cache512/group construction.

Quotient construction and ordering remain unchanged. Eligible calls use checked
128bit scores, others use the original256bit kernel. Lazy fast workspace
allocation is included in the first eligible expand call, not setup.
"""
import sys
import time
from pathlib import Path

from compiled_quotient_adaptive128_v1_2026_10_18 import Graph as BaseGraph, BINARY, BASE_BINARY
from static_quotient_lower_bound_v1 import LowerBound as BaseLower

CACHE_ENTRIES = 512


def memory():
    return {k: int(v.split()[0]) for line in Path('/proc/self/status').read_text().splitlines()
            if ':' in line for k, v in [line.split(':', 1)] if k in ('VmSize', 'VmRSS', 'VmHWM')}


class LowerBound(BaseLower):
    def tables(self, target):
        tick = time.perf_counter()
        result = super().tables(target)
        self.table_seconds += time.perf_counter()-tick
        return result


class Graph(BaseGraph):
    def table(self, target):
        self.table_calls += 1
        if self.lower.groups[target] in self.tables:
            return super().table(target)
        tick = time.perf_counter()
        result = super().table(target)
        self.native_conversions += 1
        self.table_miss_seconds += time.perf_counter()-tick
        return result

    def cache_report(self):
        tick = time.perf_counter()
        arrays = sum(sys.getsizeof(v) for table in self.tables.values()
                     for v in (table.raw, table.floor, table.reachable))
        tuple_bytes = sum(sys.getsizeof(pair)+sum(sys.getsizeof(t) for t in pair)
                          for pair in self.lower.cache.values())
        # Deliberately a gross referenced-object sum: shared integers and None
        # are counted repeatedly, so this is not unique resident allocation.
        gross_values = sum(sys.getsizeof(v) for pair in self.lower.cache.values()
                           for table in pair for v in table)
        report = dict(fast128_calls=self.fast_calls,fallback256_calls=self.fallback_calls,fast_workspace_unavailable=self.fast_unavailable,cache_entries_limit=CACHE_ENTRIES, native_cache_entries=len(self.tables),
            lower_cache_entries=len(self.lower.cache), table_calls=self.table_calls,
            native_conversions=self.native_conversions,
            reverse_table_builds=self.lower.table_builds, lower_cache_hits=self.lower.cache_hits,
            lower_cache_evictions=self.lower.evictions,
            setup_seconds=self.setup_seconds, grouping_seconds=self.grouping_seconds,
            lower_graph_construction_seconds=self.lower_graph_seconds,
            native_workspace_construction_seconds=self.native_graph_seconds,
            native_miss_inclusive_seconds=self.table_miss_seconds,
            lower_table_inclusive_seconds=self.lower.table_seconds,
            native_array_allocated_bytes=arrays, lower_tuple_container_bytes=tuple_bytes,
            lower_values_gross_referenced_object_bytes=gross_values,
            before_setup_memory_KiB=self.before_setup_memory,
            after_setup_memory_KiB=self.after_setup_memory,
            after_feedback_memory_KiB=memory(),
            scope='Timings overlap: native miss includes lower table time. Allocated arrays include overallocation; gross Python referents double-count shared values and are not RSS. Graph/workspace/temporary heaps and cache dictionaries are additional. All accounting stays in full model process time.')
        report['report_seconds'] = time.perf_counter()-tick
        return report


def create(fields, increments, initial, nodes, node_base, weight):
    tick = time.perf_counter()
    before = memory()
    groups, domain, floor = [], {}, []
    for i, node in enumerate(nodes):
        loc = node.find('loc').attrib
        segment = node.find('segment')
        key = (int(loc.get('layer', '0')), int(loc['xlow'])//4, int(loc['ylow'])//4,
               node.get('type'), int(segment.get('segment_id')) if segment is not None else -1,
               node.get('direction', 'NONE'))
        if key not in domain:
            domain[key] = len(domain)
        groups.append(domain[key])
        span = (max(int(loc['xhigh'])-int(loc['xlow']), int(loc['yhigh'])-int(loc['ylow']))+1
                if node.get('type') in ('CHANX', 'CHANY') else 0)
        floor.append(node_base[i]+weight*span)
    grouping = time.perf_counter()-tick
    stage = time.perf_counter()
    lower = LowerBound(fields, increments, initial, floor, groups, max_targets=CACHE_ENTRIES)
    lower.table_seconds = 0.0
    lower_seconds = time.perf_counter()-stage
    stage = time.perf_counter()
    result = Graph(lower)
    result.native_graph_seconds = time.perf_counter()-stage
    result.setup_seconds = time.perf_counter()-tick
    result.grouping_seconds, result.lower_graph_seconds = grouping, lower_seconds
    result.before_setup_memory, result.after_setup_memory = before, memory()
    result.table_calls = result.native_conversions = 0
    result.table_miss_seconds = 0.0
    return result
