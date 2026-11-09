"""Explicit graph/baseline/content binding for observed timing proxies."""
from copy import deepcopy
import hashlib,json
from observed_timing_proxy import path_deltas


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def baseline_digest(baseline):
    rows=sorted([{k:r[k] for k in ('connection_id','net_id','source','sink','physical_edge_ids')} for r in baseline['connections']],key=lambda r:r['connection_id'])
    return digest({'graph':baseline['physical_graph_sha256'],'rows':rows})


def bind(graph,baseline,context):
    # Validate the baseline group joins and all covered paths before freezing.
    path_deltas(graph,baseline,baseline,context)
    frozen=deepcopy(context)
    return {'schema':'ROUTECAST_BOUND_OBSERVED_CONTEXT_V1','graph_sha256':graph.sha256,'baseline_sha256':baseline_digest(baseline),'context_sha256':digest(frozen),'context':frozen}


def evaluate(graph,baseline,candidate,bound):
    if set(bound)!={'schema','graph_sha256','baseline_sha256','context_sha256','context'} or bound['schema']!='ROUTECAST_BOUND_OBSERVED_CONTEXT_V1':raise ValueError('unbound context')
    if bound['graph_sha256']!=graph.sha256 or bound['baseline_sha256']!=baseline_digest(baseline) or bound['context_sha256']!=digest(bound['context']):raise ValueError('timing context identity changed')
    return path_deltas(graph,baseline,candidate,bound['context'])
