"""JSON-valued observer snapshots, preserving insertion order and mutable isolation."""
import copy
def _value(value):
 return value if value is None or type(value) in (str,int,float,bool) else copy.deepcopy(value)
def _record(record):
 return {k:({key:(list(value) if key=='physical_edge_ids' else _value(value)) for key,value in v.items()} if k=='answer' else _value(v)) for k,v in record.items()}
def clone_state(state):
 if state is None:return None
 return {k:([_record(record) for record in v] if k=='records' else copy.deepcopy(v)) for k,v in state.items()}
def clone_states(states):
 return {net:clone_state(state) for net,state in states.items()}
