"""Exact rational directional bbox demand proxy, not physical occupancy."""
from collections import defaultdict
from fractions import Fraction
from incremental_net_geometry import GeometryState


def contribution(records, locations):
    points = [locations[n] for _, source, sink in records for n in (source, sink)]
    left, right = min(p[0] for p in points), max(p[0] for p in points)
    bottom, top = min(p[1] for p in points), max(p[1] for p in points)
    area = (right-left+1)*(top-bottom+1)
    horizontal, vertical = Fraction(right-left, area), Fraction(top-bottom, area)
    return {(x,y,d): value for x in range(left,right+1) for y in range(bottom,top+1)
            for d,value in ((0,horizontal),(1,vertical)) if value}


class DensityState:
    def __init__(self, rows, locations):
        self.geometry = GeometryState(rows, locations)
        self.by_net = {net: contribution(records.values(), locations)
                       for net, records in self.geometry.nets.items()}
        demand = defaultdict(Fraction)
        for values in self.by_net.values():
            for cell,value in values.items(): demand[cell] += value
        self.demand = dict(demand)

    def trial(self, replacements, epoch):
        geometry = self.geometry.trial(replacements, epoch)
        contributions = {net: contribution(records.values(), self.geometry.locations)
                         for net,records in geometry['nets'].items()}
        delta = defaultdict(Fraction)
        for net, values in contributions.items():
            for cell,value in self.by_net[net].items(): delta[cell] -= value
            for cell,value in values.items(): delta[cell] += value
        changes = {cell:self.demand.get(cell,Fraction())+value for cell,value in delta.items() if value}
        assert all(value >= 0 for value in changes.values())
        return geometry, contributions, changes

    def update(self, replacements, epoch):
        replacements = list(replacements)
        trial, contributions, changes = self.trial(replacements, epoch)
        # Revalidation precedes all mutation; there is no exposed commit token.
        self.geometry.update(replacements, epoch)
        self.by_net.update(contributions)
        for cell,value in changes.items():
            if value: self.demand[cell] = value
            else: self.demand.pop(cell,None)
        return {'dirty_nets':len(contributions),'changed_cells':len(changes)}
