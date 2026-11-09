"""Exact buffered RC path evaluation over authenticated CSR and node classes.

Caller authenticates both payloads. No full edge-weight vector or reverse map.
This is connection expansion delay, without route-tree branching load or STA.
"""
from fractions import Fraction
from buffered_rc_node_classes import arc_delay

class ExactBufferedRC:
    def __init__(self, fields, node_classes, classes, switches):
        n=len(node_classes)
        if len(fields['node_ids'])!=n or any(v!=i for i,v in enumerate(fields['node_ids'])):
            raise ValueError('contiguous raw node identities required')
        if len(fields['row_offsets'])!=n+1 or fields['row_offsets'][-1]!=len(fields['edge_ids']):
            raise ValueError('CSR dimension mismatch')
        if any(v>=len(classes) for v in node_classes):raise ValueError('unknown RC class')
        self.fields=fields;self.node_classes=node_classes;self.classes=classes;self.switches=switches;self.cache={}
    def node(self,n):
        if type(n) is not int or not 0<=n<len(self.node_classes):raise ValueError('invalid raw node')
        return self.classes[self.node_classes[n]]
    def increment(self,index):
        f=self.fields
        if type(index) is not int or not 0<=index<len(f['edge_ids']):raise ValueError('invalid CSR arc index')
        k=(self.node_classes[f['dest_ranks'][index]],f['switch_ids'][index])
        if k not in self.cache:self.cache[k]=arc_delay(self.classes,self.switches,*k)
        return self.cache[k]
    def path(self,source,sink,edge_ids):
        r,c=self.node(source);self.node(sink);delay=r*c/2;current=source;seen={source};f=self.fields
        for eid in edge_ids:
            if type(eid) is not int or eid<0:raise ValueError('invalid raw edge ID')
            matches=[i for i in range(f['row_offsets'][current],f['row_offsets'][current+1]) if f['edge_ids'][i]==eid]
            if len(matches)!=1:raise ValueError('discontinuous or ambiguous raw edge')
            i=matches[0];current=f['dest_ranks'][i]
            if current in seen:raise ValueError('cyclic path')
            seen.add(current);delay+=self.increment(i)
        if current!=sink:raise ValueError('wrong terminal')
        if not isinstance(delay,Fraction):raise ValueError('nonexact RC context')
        return delay
