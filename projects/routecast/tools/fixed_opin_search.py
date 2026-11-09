"""Constrain all SOURCE exits to one physical OPIN without resetting RC delay."""
from csr_integer_exact_delay import query

def fixed_opin_query(context,source,sink,opin,budget,allowed,max_nodes=100000):
 f=context.fields
 for node in (source,sink,opin):context.rc.node(node)
 if f['types'][source]!=0 or f['types'][sink]!=1 or f['types'][opin]!=2:
  raise ValueError('expected SOURCE, SINK, OPIN')
 arcs=[i for i in range(f['row_offsets'][source],f['row_offsets'][source+1]) if f['dest_ranks'][i]==opin]
 if not arcs:raise ValueError('OPIN is not a direct SOURCE member')
 def constrained(node,index):
  if node==source and f['dest_ranks'][index]!=opin:return False
  return allowed(node,index)
 result=query(context,source,sink,budget,constrained,max_nodes=max_nodes)
 if result['status']=='FOUND':
  assert result['physical_edge_ids'] and result['physical_edge_ids'][0] in {f['edge_ids'][i] for i in arcs}
 return result
