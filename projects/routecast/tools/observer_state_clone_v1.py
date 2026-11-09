"""JSON-valued observer snapshots: exact values and independent mutable containers."""
import copy
from tree_floor_pareto_affected_seed_v13 import _copy_records
def clone_state(state):
 if state is None:return None
 return {k:(_copy_records(v) if k=='records' else copy.deepcopy(v)) for k,v in state.items()}
def clone_states(states):
 return {net:clone_state(state) for net,state in states.items()}
