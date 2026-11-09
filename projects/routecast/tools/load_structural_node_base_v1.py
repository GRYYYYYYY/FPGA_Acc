"""Authenticated node-base input owned by the structural model."""
import json,sys
from pathlib import Path
from array import array
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
PROOF=R/'experiments/mmc_native_node_base_mapping_v1_2026-10-10/verification.json'
def load(n,scale):
 v=json.loads(PROOF.read_text());assert v['nodes']==n and v['scale']==scale and v['array_byteorder']==sys.byteorder
 assert v['all_original_node_ids_types_segments_and_native_group_counts_pass'] and all(sha(p)==h for p,h in v['bindings'].items())
 path=PROOF.parent/'node_base.u64';values=array('Q');values.frombytes(path.read_bytes());assert len(values)==n
 return tuple(values),{**v['bindings'],str(PROOF):sha(PROOF)}
