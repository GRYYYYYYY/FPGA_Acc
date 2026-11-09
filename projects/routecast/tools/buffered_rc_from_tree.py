"""Exact electrical classes from an already parsed authenticated RR tree.

Caller must authenticate graph bytes before/after the complete build. This
function reads only the supplied snapshot and does not establish file identity.
"""
from array import array
from path_rc import number

def read_tree(xml):
 if xml.tag!='rr_graph':raise ValueError('expected RR root')
 indices=array('Q');classes=[];lookup={};switches={}
 nodes=xml.find('rr_nodes');switch_container=xml.find('switches')
 if nodes is None or switch_container is None:raise ValueError('missing RR section')
 for node in nodes:
  if node.tag!='node':continue
  if int(node.get('id'))!=len(indices):raise ValueError('contiguous node IDs required')
  timing=node.find('timing')
  if timing is None or not {'R','C'}<=set(timing.attrib):raise ValueError('missing node RC')
  key=(timing.get('R'),timing.get('C'))
  if key not in lookup:
   resistance,capacitance=map(number,key);lookup[key]=len(classes);classes.append((resistance,capacitance))
  indices.append(lookup[key])
 for node in switch_container:
  if node.tag!='switch':continue
  sid=int(node.get('id'));timing=node.find('timing')
  if sid<0 or sid in switches or timing is None:raise ValueError('invalid switch')
  if node.get('type') not in {'buffer','mux','tristate'}:raise ValueError('nonbuffered switch')
  if number(timing.get('Cinternal','0')):raise ValueError('nonzero Cinternal')
  switches[sid]=(number(timing.get('R','0')),number(timing.get('Tdel','0')))
 if not indices or not switches:raise ValueError('empty electrical context')
 return indices,classes,switches
