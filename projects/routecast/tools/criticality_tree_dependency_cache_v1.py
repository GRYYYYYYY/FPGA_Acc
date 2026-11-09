"""Experimental exact read-dependency cache for the arbitrary-integer reference.

Extends the earlier standalone128 cache idea to criticality, retained multi-source
seed state and raw budgets. Prices must be a pure, stable serial total snapshot.
No compiled/live model integration or concurrent/impure callback guarantee.
"""
import copy
from collections import Counter,OrderedDict
from fractions import Fraction
from criticality_shared_tree_sparse_reference_v3 import Graph as ReferenceGraph,Tree as ReferenceTree


class Reads:
    def __init__(self,prices,limit):
        self.prices=prices;self.limit=limit;self.values={};self.complete=True
    def get(self,node,default=0):
        value=self.prices.get(node,default)
        if node not in self.values:
            if len(self.values)<self.limit:self.values[node]=value
            else:self.complete=False
        return value


class Graph(ReferenceGraph):
    def __init__(self,fields,increments,initial,*,entries=128,read_limit=65536,state_limit=16384,total_limit=262144):
        for value in (entries,read_limit,state_limit,total_limit):
            if type(value) is not int or value<0:raise ValueError('nonnegative integer cache bound')
        super().__init__(fields,increments,initial)
        self.entries,self.read_limit,self.state_limit,self.total_limit=entries,read_limit,state_limit,total_limit
        self.cache=OrderedDict();self.items=0;self.stats=Counter()
    def tree(self,source):
        base=super().tree(source)
        tree=Tree.__new__(Tree);tree.__dict__.update(base.__dict__);tree.owner=self
        return tree
    def discard(self,key):
        old=self.cache.pop(key,None)
        if old is not None:self.items-=old['items']


class Tree(ReferenceTree):
    def expand(self,target,criticality,congestion,raw_budget):
        owner=self.owner
        if any(getattr(self,k) is not v for k,v in owner._snapshot.items()):raise ValueError('graph snapshot rebound')
        if type(target) is not int or not 0<=target<self.n:raise ValueError('target')
        if not isinstance(criticality,Fraction) or not 0<=criticality<=1:raise ValueError('criticality')
        if not hasattr(congestion,'get'):raise ValueError('price getter')
        if type(raw_budget) is not int or raw_budget<0:raise ValueError('raw budget')
        size=len(self.arrival)+len(self.parents)
        if size>owner.state_limit or not owner.entries:
            owner.stats['uncached_seed_or_disabled']+=1;owner.stats['actual_searches']+=1
            return super().expand(target,criticality,congestion,raw_budget)
        # Whole pre-search seed, graph instance, criticality and raw budget are
        # part of the key. Epoch/NET names alone are not seed-state identities.
        key=(self.source,target,criticality.numerator,criticality.denominator,raw_budget,tuple(sorted(self.arrival.items())),tuple(sorted(self.parents.items())))
        old=owner.cache.get(key)
        if old is not None:
            valid=True
            for node,previous in old['reads']:
                value=congestion.get(node,0)
                if type(value) is not int or value<0 or value!=previous:valid=False;break
            if valid:
                owner.stats['hits']+=1;owner.cache.move_to_end(key)
                self.arrival=dict(old['arrival']);self.parents=dict(old['parents'])
                return copy.deepcopy(old['result'])
        owner.discard(key);owner.stats['misses']+=1;owner.stats['actual_searches']+=1
        reads=Reads(congestion,owner.read_limit)
        result=super().expand(target,criticality,reads,raw_budget)
        output_size=len(self.arrival)+len(self.parents)+len(result.get('path_slots',()))
        items=size+len(reads.values)+output_size
        if not reads.complete:
            owner.stats['incomplete_read_trace']+=1;return result
        if output_size>owner.state_limit or items>owner.total_limit:
            owner.stats['oversize_entry']+=1;return result
        entry=dict(reads=tuple(sorted(reads.values.items())),arrival=dict(self.arrival),parents=dict(self.parents),result=copy.deepcopy(result),items=items)
        owner.cache[key]=entry;owner.items+=items
        while len(owner.cache)>owner.entries or owner.items>owner.total_limit:
            first=next(iter(owner.cache));owner.discard(first);owner.stats['evictions']+=1
        return result
