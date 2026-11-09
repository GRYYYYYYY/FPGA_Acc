"""Native printed work counters; rounded internal times are descriptive only."""
import re
from decimal import Decimal

ROW = re.compile(r'^\s*(\d+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\(\s*([0-9.eE+-]+)%\)\s+(\d+)\s+\(\s*([0-9.eE+-]+)%\)\s+([0-9.eE+-]+)\s+')

def extract(text):
    rows=[];table=False
    for line in text.splitlines():
        if line.startswith('Iter   Time') and 'Overused RR Nodes' in line:
            if table or rows:raise ValueError('multiple routing tables unsupported')
            table=True
        if table:
            m=ROW.match(line)
            if m:
                vals=m.groups();rows.append(dict(iteration=int(vals[0]),printed_time_seconds=vals[1],heap_pushes=int(vals[4]),rerouted_nets=int(vals[5]),rerouted_connections=int(vals[6]),overused_nodes=int(vals[7]),wirelength=int(vals[9]),printed_cpd_ns=vals[11]))
            elif line.startswith('Restoring best routing') or line.startswith('Successfully routed after'):
                table=False
    success=re.findall(r'Successfully routed after (\d+) routing iterations\.',text)
    if success:
        if len(success)!=1 or not rows or [x['iteration'] for x in rows]!=list(range(1,int(success[0])+1)):
            raise ValueError('incomplete iteration evidence')
        if rows[-1]['overused_nodes']!=0:raise ValueError('success with overused resources')
    def last(pattern):
        values=re.findall(pattern,text,re.M)
        return values[-1] if values else None
    return dict(iterations=int(success[0]) if success else None,iteration_rows=rows,
                printed_path_search_seconds=last(r'Time spent on path search: ([0-9.eE+-]+) seconds'),
                printed_routing_seconds=last(r'^# Routing took ([0-9.eE+-]+) seconds'),
                printed_vpr_flow_seconds=last(r'The entire flow of VPR took ([0-9.eE+-]+) seconds'),
                heap_pushes=sum(x['heap_pushes'] for x in rows) if rows else None,
                rerouted_connection_attempts=sum(x['rerouted_connections'] for x in rows) if rows else None,
                routing_success=bool(success),native_vpr_succeeded='VPR succeeded' in text)
