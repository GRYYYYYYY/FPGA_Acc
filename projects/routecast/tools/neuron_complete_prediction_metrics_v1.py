"""Full-domain descriptive metrics; caller must independently admit native truth."""
from stream_metric_domain_layered_v1 import metric_domain
from prediction_metrics import compare


def evaluate(graph_path, initial_occupancy, sketch_occupancy, native_occupancy):
    results={}
    universe=None
    for name, prediction in (('initial',initial_occupancy),('sketch',sketch_occupancy)):
        p,t,sp,st,_,counts=metric_domain(graph_path,prediction,native_occupancy)
        current=(set(p),set(sp))
        if universe is not None and current!=universe:
            raise ValueError('frame metric universes differ')
        universe=current
        results[name]=dict(concrete=compare(p,t,max(1,(len(t)+19)//20)),
                           spatial=compare(sp,st,20),original_node_counts=counts)
    return dict(metrics=results,heldout_family_certified=False,
                scope='Complete channel/span descriptive metrics only; caller must audit native legality, unique-NET occupancy and demand semantics. No QoR or end-to-end gain claim.')
