"""Prepared immutable-graph template indexes for repeated endpoint cohorts.

Search/ledger state is recreated per call; only graph, partition, costs and
physical witnesses persist. Costs/budget/refinement are fixed for the instance.
"""
from collections import Counter,defaultdict
from types import MappingProxyType
from connection_golden import Result
from rr_occupancy import Occupancy
from semantic_sketch import Sketch
from template_sketch import quotient
from template_connectivity import Lifter,refine


class WitnessIndex(dict):
    def __missing__(self,key):return ()


class PreparedTemplates:
    def __init__(self,graph,rounds=2,search_type=Sketch):
        coarse,mapping,_=quotient(graph,True)
        pooled,mapping,members,performed,is_stable=refine(graph,coarse,mapping,rounds)
        self.graph=graph;self.rounds=rounds;self.pooled=pooled
        self.mapping=MappingProxyType(mapping);self.performed=performed;self.stable=is_stable
        self.sketch=search_type(pooled,'rr_length_switch',len(pooled.nodes))
        self.lifter=Lifter(graph,pooled,self.mapping)
        self.lifter.witness=WitnessIndex({k:tuple(v) for k,v in self.lifter.witness.items()})

    def predict(self,endpoints):
        if endpoints.get('graph_sha256')!=self.graph.sha256:raise ValueError('endpoint graph identity mismatch')
        graph=self.graph;rounds=self.rounds;pooled=self.pooled;mapping=self.mapping
        performed=self.performed;is_stable=self.stable;sketch=self.sketch;lifter=self.lifter
        ledger=Occupancy(graph);groups=defaultdict(list);rows=[];search_work=Counter()
        for row in endpoints['connections']:groups[row['source']].append(row)
        for source,connections in sorted(groups.items()):
            result=sketch.search(mapping[source],{mapping[r['sink']] for r in connections})
            search_work['settled_nodes']+=result.settled_nodes;search_work['edge_visits']+=result.edge_visits
            lifted={}
            for row in connections:
                sink=row['sink'];path=result.paths.get(mapping[sink])
                if path is None:raise AssertionError('native reachable endpoints missing from quotient')
                if sink not in lifted:lifted[sink]=lifter.lift(source,sink,path)
                lifted_result=lifted[sink]
                if lifted_result.edge_ids is not None:
                    if ledger.update(row['connection_id'],1,row['net_id'],source,sink,lifted_result.edge_ids)!=Result.COMMITTED:
                        raise AssertionError('physical witness rejected by ledger')
                rows.append({**row,'quotient_edge_ids':path,'physical_edge_ids':lifted_result.edge_ids,
                             'failed_at':lifted_result.failed_at,'frontier_sizes':lifted_result.frontier_sizes,
                             'witness_edge_visits':lifted_result.physical_edge_visits})
            search_work['witness_edge_visits']+=sum(r.physical_edge_visits for r in lifted.values())
        if ledger.occupancy!=ledger.rebuild():raise AssertionError('lifted physical demand mismatch')
        failures=[r for r in rows if r['physical_edge_ids'] is None]
        if is_stable and failures:raise AssertionError('fixed-point quotient path cannot be lifted')
        return {'physical_graph_sha256':graph.sha256,'quotient_graph_sha256':pooled.sha256,'requested_rounds':rounds,
                'performed_rounds':performed,'stable_partition':is_stable,'nodes':len(pooled.nodes),'edges':len(pooled.edges),
                'requested_connections':len(rows),'lifted_connections':len(rows)-len(failures),
                'failures_by_step':dict(Counter(r['failed_at'] for r in failures)),'connections':rows,
                'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'work':dict(search_work),
                'scope':'exact individual RR switch/arc paths; no joint net capacity, VPR route-tree or closure guarantee'}
