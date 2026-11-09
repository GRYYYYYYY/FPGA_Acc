"""VPR work table including rounded scientific-notation heap counts.

Scientific notation is retained as printed evidence, never an exact work count.
"""
import re
from decimal import Decimal

NUMBER = r'[0-9.eE+-]+'
ROW = re.compile(r'^\s*(\d+)\s+(' + NUMBER + r')\s+(' + NUMBER + r')\s+(\d+)\s+('
                 + NUMBER + r')\s+(\d+)\s+(\d+)\s+(\d+)\s+\(\s*(' + NUMBER
                 + r')%\)\s+(\d+)\s+\(\s*(' + NUMBER + r')%\)\s+(' + NUMBER + r')\s+')


def extract(text):
    rows = []
    table = False
    for line in text.splitlines():
        if line.startswith('Iter   Time') and 'Overused RR Nodes' in line:
            if table or rows:
                raise ValueError('multiple routing tables unsupported')
            table = True
        if table:
            m = ROW.match(line)
            if m:
                v = m.groups()
                count = Decimal(v[4])
                if not count.is_finite() or count < 0 or count != count.to_integral_value():
                    raise ValueError('invalid printed heap count')
                exact = v[4].isdigit()
                rows.append(dict(iteration=int(v[0]), printed_time_seconds=v[1],
                    heap_pushes=int(count) if exact else None,
                    printed_heap_pushes=v[4], printed_heap_pushes_is_exact=exact,
                    rerouted_nets=int(v[5]), rerouted_connections=int(v[6]),
                    overused_nodes=int(v[7]), wirelength=int(v[9]), printed_cpd_ns=v[11]))
            elif line.startswith('Restoring best routing') or line.startswith('Successfully routed after'):
                table = False
    success = re.findall(r'Successfully routed after (\d+) routing iterations\.', text)
    if success:
        if len(success) != 1 or not rows or [r['iteration'] for r in rows] != list(range(1, int(success[0]) + 1)):
            raise ValueError('incomplete iteration evidence')
        if rows[-1]['overused_nodes'] != 0:
            raise ValueError('success with overused resources')
    def last(pattern):
        values = re.findall(pattern, text, re.M)
        return values[-1] if values else None
    exact = bool(rows) and all(r['printed_heap_pushes_is_exact'] for r in rows)
    return dict(iterations=int(success[0]) if success else None, iteration_rows=rows,
        printed_path_search_seconds=last(r'Time spent on path search: ([0-9.eE+-]+) seconds'),
        printed_routing_seconds=last(r'^# Routing took ([0-9.eE+-]+) seconds'),
        printed_vpr_flow_seconds=last(r'The entire flow of VPR took ([0-9.eE+-]+) seconds'),
        heap_pushes=sum(r['heap_pushes'] for r in rows) if exact else None,
        printed_heap_pushes_sum=sum(int(Decimal(r['printed_heap_pushes'])) for r in rows) if rows else None,
        heap_pushes_exact=exact,
        rerouted_connection_attempts=sum(r['rerouted_connections'] for r in rows) if rows else None,
        routing_success=bool(success), native_vpr_succeeded='VPR succeeded' in text)
