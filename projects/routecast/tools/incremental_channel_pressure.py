"""Affected-node cache for normalized channel overuse; caller authenticates graph/dirty set."""
class ChannelPressure:
    def __init__(self, types, capacities):
        if len(types)!=len(capacities):raise ValueError('dimension mismatch')
        self.types=types;self.capacities=capacities;self.rows={}

    def refresh(self, occupancy, dirty_nodes):
        staged={}
        for node in set(dirty_nodes):
            if type(node) is not int or not 0<=node<len(self.types):raise ValueError('invalid node')
            value=occupancy.get(node,0);cap=self.capacities[node]
            if type(value) is not int or value<0:raise ValueError('invalid occupancy')
            staged[node]=(cap,1+(value-cap)/cap) if self.types[node] in (4,5) and cap>0 and value>cap else None
        for node,value in staged.items():
            if value is None:self.rows.pop(node,None)
            else:self.rows[node]=value

    def payload(self, graph_sha256):
        if len(graph_sha256)!=64 or any(c not in '0123456789abcdef' for c in graph_sha256):raise ValueError('invalid graph digest')
        return f'ROUTECAST_PRESSURE_V1 {len(self.types)} {graph_sha256}\n'+''.join(f'{node} {cap} {value:.9g}\n' for node,(cap,value) in sorted(self.rows.items()))
