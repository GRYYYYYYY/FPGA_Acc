"""Repair failed quotient lifts with regional RR search, then full RR fallback.

Only failed endpoint pairs are searched; 'regional' means RR node extents overlap
an endpoint bounding box plus margin. Long segments may extend outside that box.
Physical arc paths remain congestion-unaware, not a legal multi-net router.
"""
from collections import Counter, defaultdict
from copy import copy
from dataclasses import replace
from connection_golden import Result
from rr_occupancy import Occupancy
from semantic_sketch import Sketch


class RegionalSearch:
    def __init__(self,graph,margin=1):
        if type(margin) is not int or margin<0:raise ValueError('invalid region margin')
        self.graph=graph;self.margin=margin;self.engine=Sketch(graph,'rr_length_switch',len(graph.nodes))
        self.locations={}
        for nid,node in graph.nodes.items():
            loc=dict(node.location)
            self.locations[nid]=tuple(int(loc.get(k,'0')) for k in ('xlow','xhigh','ylow','yhigh','layer'))

    def search(self,source,sinks):
        sinks=set(sinks)
        endpoints=[self.locations[n] for n in {source}|sinks]
        if len({loc[4] for loc in endpoints})!=1:raise ValueError('regional multi-layer repair unsupported')
        layer=endpoints[0][4]
        box=(min(loc[0] for loc in endpoints)-self.margin,max(loc[1] for loc in endpoints)+self.margin,
             min(loc[2] for loc in endpoints)-self.margin,max(loc[3] for loc in endpoints)+self.margin)
        allowed={n for n,(xl,xh,yl,yh,z) in self.locations.items()
                 if z==layer and xl<=box[1] and xh>=box[0] and yl<=box[3] and yh>=box[2]}
        view=copy(self.engine);view.adjacency={};probes=0
        for n in allowed:
            original=self.engine.adjacency[n];probes+=len(original)
            view.adjacency[n]=[eid for eid in original if self.graph.edges[eid].sink in allowed]
        result=view.search(source,sinks)
        if result.budget_exhausted:raise AssertionError('regional node budget unexpectedly exhausted')
        return result,{'box':box,'allowed_nodes':len(allowed),'region_node_tests':len(self.locations),
                       'adjacency_filter_probes':probes}


def repair(graph,endpoints,candidates,margin=1,*,search_type=RegionalSearch):
    if endpoints['graph_sha256']!=graph.sha256 or candidates['physical_graph_sha256']!=graph.sha256:
        raise ValueError('graph identity mismatch')
    fields=('connection_id','net_id','source','sink')
    expected={r['connection_id']:tuple(r[k] for k in fields) for r in endpoints['connections']}
    if len(expected)!=len(endpoints['connections']):raise ValueError('duplicate endpoint connection ID')
    seen={};pending=defaultdict(set)
    for r in candidates['connections']:
        cid=r['connection_id']
        if cid in seen or expected.get(cid)!=tuple(r[k] for k in fields):raise ValueError('candidate cohort mismatch')
        seen[cid]=r
        if r['physical_edge_ids'] is None:pending[r['source']].add(r['sink'])
    if set(seen)!=set(expected):raise ValueError('candidate cohort incomplete')
    regional=search_type(graph,margin) if pending else None
    resolved={};traces=[];work=Counter()
    for source,sinks in sorted(pending.items()):
        local,details=regional.search(source,sinks)
        remaining=sinks-set(local.paths)
        work['region_node_tests']+=details['region_node_tests']
        work['adjacency_filter_probes']+=details['adjacency_filter_probes']
        work['regional_settled_nodes']+=local.settled_nodes;work['regional_edge_visits']+=local.edge_visits
        for sink,path in local.paths.items():resolved[(source,sink)]=(path,'regional')
        if remaining:
            full=regional.engine.search(source,remaining)
            work['full_settled_nodes']+=full.settled_nodes;work['full_edge_visits']+=full.edge_visits
            for sink,path in full.paths.items():resolved[(source,sink)]=(path,'full')
        traces.append({'source':source,'failed_unique_endpoints':len(sinks),'regional_resolved':len(local.paths),
                       'full_requested':len(remaining),'details':details})
    ledger=Occupancy(graph);rows=[]
    for row in sorted(endpoints['connections'],key=lambda r:r['connection_id']):
        original=seen[row['connection_id']];path=original['physical_edge_ids'];method='lifted'
        if path is None:path,method=resolved.get((row['source'],row['sink']),(None,'failed'))
        if path is not None:
            result=ledger.update(row['connection_id'],1,row['net_id'],row['source'],row['sink'],path)
            if result!=Result.COMMITTED:raise ValueError('final physical path rejected by ledger')
        rows.append({**row,'physical_edge_ids':path,'method':method})
    if ledger.occupancy!=ledger.rebuild():raise AssertionError('hybrid net-union mismatch')
    count=Counter(r['method'] for r in rows)
    return {'schema':'ROUTECAST_HYBRID_REPAIR_V1','physical_graph_sha256':graph.sha256,'margin':margin,
            'connections':rows,'methods':dict(count),'requested':len(rows),'completed':len(rows)-count['failed'],
            'repair_sources':len(pending),'repair_traces':traces,'repair_work':dict(work),
            'candidate_work':candidates['work'],
            'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},
            'scope':'independent physical arc paths plus per-net accounting; no negotiated congestion or VPR legality claim'}
