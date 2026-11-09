"""Deterministic per-path certified-delay target selection, without outcome tuning."""
import re

def select_targets(paths,input_bindings,output_bindings,minimum_records,limit=3,internal_bindings=()):
 if type(limit) is not int or limit<1:raise ValueError('positive path limit required')
 inputs={}
 for row in input_bindings:
  key=(row['atom'],row['logical_bit']);cid=row['connection_id']
  if key in inputs and inputs[key]!=cid:raise ValueError('ambiguous atom pin binding')
  inputs[key]=cid
 outputs={}
 for row in output_bindings:
  name=row['net_name'];cid=row['connection_id']
  if name in outputs and outputs[name]!=cid:raise ValueError('ambiguous output binding')
  outputs[name]=cid
 minima={}
 for row in minimum_records:
  cid=row['query']['connection_id']
  if cid in minima:raise ValueError('duplicate minimum certificate')
  minima[cid]=row
 internal={(x['atom'],x['logical_bit']) for x in internal_bindings if x['external_cluster_input'] is None}
 selected=[];ranks=[]
 for rank,path in enumerate(paths[:limit],1):
  cohort=set();unbound=[]
  for step in path['steps']:
   m=re.fullmatch(r'(.+)\.in\[(\d+)\] \(\.names\)',step['to'])
   o=re.fullmatch(r'out:(.+)\.outpad\[0\] \(\.output\)',step['to'])
   if m:
    key=(m[1],int(m[2]))
    if key in inputs:cohort.add(inputs[key])
    elif key in internal:unbound.append({'atom':key[0],'logical_bit':key[1],'classification':'packed_internal'})
    else:raise ValueError('unresolved logical input binding')
   elif o:
    if o[1] not in outputs:raise ValueError('output terminal binding missing')
    cohort.add(outputs[o[1]])
  if not cohort or not cohort<=minima.keys():raise ValueError('external cohort certificate missing')
  eligible=[cid for cid in cohort if minima[cid]['old_delay_integer']>minima[cid]['delay_integer']]
  winner=min(eligible,key=lambda cid:(-(minima[cid]['old_delay_integer']-minima[cid]['delay_integer']),cid)) if eligible else None
  if winner is not None and winner not in selected:selected.append(winner)
  ranks.append({'path_rank':rank,'endpoint':path['endpoint'],'connection_cohort':sorted(cohort),'internal_or_unbound':unbound,'selected_connection_id':winner})
 return {'target_connection_ids':selected,'rank_selection':ranks}
