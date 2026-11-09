"""Single-target directed nonnegative-cost reference; no tree equivalence claim."""
import heapq

class Bidirectional:
    def __init__(self, fields, increments):
        self.fields, self.increments = fields, increments
        self.incoming = [[] for _ in fields['capacities']]
        for u in range(len(self.incoming)):
            for e in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
                self.incoming[fields['dest_ranks'][e]].append((u,e))

    def search(self, source, sink, prices, weight, initial=0):
        f, inc = self.fields, self.increments
        n = len(f['capacities'])
        assert 0 <= source < n and 0 <= sink < n
        assert f['capacities'][source] and f['capacities'][sink]
        assert weight >= 0 and initial >= 0 and all(x >= 0 for x in inc)
        assert all(x >= 0 for x in prices.values())
        distances = [{source:0},{sink:0}]
        queues = [[(0,source)],[(0,sink)]]
        parents = [{},{}]
        best, meet = None, None
        scanned = [0,0]
        settled = [set(),set()]
        def bound(node):
            nonlocal best, meet
            if node in distances[0] and node in distances[1]:
                value = distances[0][node]+distances[1][node]
                if best is None or value < best:
                    best,meet = value,node
        bound(source)
        while True:
            for side in range(2):
                q = queues[side]
                while q and (q[0][0]!=distances[side][q[0][1]] or q[0][1] in settled[side]):
                    heapq.heappop(q)
            if not queues[0] or not queues[1]:
                break
            if best is not None and queues[0][0][0]+queues[1][0][0] >= best:
                break
            side = int(queues[1][0] < queues[0][0])
            cost,u = heapq.heappop(queues[side])
            settled[side].add(u)
            arcs = ([(f['dest_ranks'][e],e) for e in range(f['row_offsets'][u],f['row_offsets'][u+1])]
                    if side==0 else self.incoming[u])
            for v,e in arcs:
                scanned[side] += 1
                if not f['capacities'][v]:
                    continue
                destination = v if side==0 else u
                value = cost+inc[e]+weight*prices.get(destination,0)
                old = distances[side].get(v)
                if old is None or value < old:
                    distances[side][v] = value
                    parents[side][v] = (u,e)
                    heapq.heappush(queues[side],(value,v))
                    bound(v)
        if best is None:
            return None
        path,u = [],meet
        while u!=source:
            u,e = parents[0][u]
            path.append(e)
        path.reverse()
        u = meet
        while u!=sink:
            u,e = parents[1][u]
            path.append(e)
        # Joining optimal halves can include a zero-cost cycle. Erase only
        # cycles whose full current weighted cost is independently zero.
        vertices, slots, positions = [source],[],{source:0}
        for e in path:
            u = vertices[-1]
            assert f['row_offsets'][u]<=e<f['row_offsets'][u+1]
            v = f['dest_ranks'][e]
            if v in positions:
                k = positions[v]
                removed = slots[k:]+[e]
                assert sum(inc[x]+weight*prices.get(f['dest_ranks'][x],0) for x in removed)==0
                for node in vertices[k+1:]:
                    del positions[node]
                del vertices[k+1:]
                del slots[k:]
            else:
                slots.append(e)
                positions[v] = len(vertices)
                vertices.append(v)
        assert vertices[-1]==sink
        objective = initial+sum(inc[e]+weight*prices.get(f['dest_ranks'][e],0) for e in slots)
        assert objective==initial+best
        return dict(slots=slots,objective=objective,raw=initial+sum(inc[e] for e in slots),
                    scanned_arcs=scanned,settled_nodes=list(map(len,settled)))
