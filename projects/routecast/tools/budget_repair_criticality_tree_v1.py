"""Original compiled primary, bounded repair only on post-search raw rejection."""
from compiled_criticality_tree_v1 import Graph as OriginalGraph, Tree as OriginalTree
from reverse_raw_delay_bounds_v1 import ReverseBounds
from weighted_budget_pareto_search_v1 import search

class Graph(OriginalGraph):
    def __init__(self,fields,increments,initial):
        super().__init__(fields,increments,initial)
        self.capacities=tuple(fields['capacities']);self.repair_bounds=None;self.repair_events=[];self.repair_label_limit=10000
    def tree(self,source):
        if self.closed or type(source) is not int or not 0<=source<self.n:raise ValueError('closed graph or invalid source')
        return Tree(self,source)

class Tree(OriginalTree):
    def expand(self,target,criticality,congestion,raw_budget):
        original=super().expand(target,criticality,congestion,raw_budget)
        if original['status']!='RETAIN_RAW_BUDGET':return original
        g=self.graph
        if g.repair_bounds is None:g.repair_bounds=ReverseBounds(g.offsets,g.dest,g.inc)
        hits=g.repair_bounds.hits;bound=g.repair_bounds.bound(target,raw_budget)
        result=search(self.offsets,self.dest,self.inc,g.capacities,self.arrival,target,criticality,congestion,raw_budget,bound,max_labels=g.repair_label_limit)
        meta=dict(source=self.source,target=target,budget=raw_budget,criticality_numerator=criticality.numerator,criticality_denominator=criticality.denominator,original_raw=original['raw'],original_objective_numerator=original['objective_numerator'],original_objective_denominator=original['objective_denominator'],initial_arrivals=sorted(self.arrival.items()),bound_context_sha256=bound.context,bound_target=bound.target,bound_cap=bound.cap,bound_cache_hit=g.repair_bounds.hits>hits,label_limit=g.repair_label_limit,**result)
        if result['status']!='FOUND':
            g.repair_events.append(meta)
            return dict(status=result['status'],committed=False,repair_index=len(g.repair_events)-1)
        join=result['join'];tail=result['path_slots'];prefix=[];u=join
        while u!=self.source:
            parent,edge=self.parents[u];prefix.append(edge);u=parent
        prefix.reverse();value=self.arrival[join];seen=set(self.arrival);updates=[];u=join;tail_prices=[]
        for edge in tail:
            assert self.offsets[u]<=edge<self.offsets[u+1];v=self.dest[edge];assert v not in seen and g.capacities[v]>0;seen.add(v);value+=self.inc[edge];updates.append((v,u,edge,value));tail_prices.append((v,congestion.get(v,0)));u=v
        assert u==target and value==result['raw']<=raw_budget
        p,q=criticality.numerator,criticality.denominator
        assert result['objective_numerator']==p*value+(q-p)*sum(price for node,price in tail_prices)
        meta['tail_node_prices']=tail_prices;g.repair_events.append(meta)
        for node,parent,edge,arrival in updates:self.parents[node]=(parent,edge);self.arrival[node]=arrival
        return dict(status='COMMITTED',committed=True,raw=value,objective_numerator=result['objective_numerator'],objective_denominator=q,attach=join,new_nodes=len(tail),path_slots=tuple(prefix)+tail,repair_index=len(g.repair_events)-1)
