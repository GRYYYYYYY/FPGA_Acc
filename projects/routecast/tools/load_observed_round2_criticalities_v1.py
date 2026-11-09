"""Privileged observed-round2 diagnostic vector; unobserved values explicitly carried."""
import json,struct,math
from pathlib import Path
from types import MappingProxyType
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
DIRECTORY=R/'experiments/mmc_observed_round2_criticality_input_v1_2026-10-12'
def load():
 proof=DIRECTORY/'verification_v1.json';v=json.loads(proof.read_text())
 assert v['all115572_identity_float32_values_and_provenance_pass']
 assert all(sha(p)==h for p,h in v['bindings'].items())
 path=DIRECTORY/'connections.json';assert sha(path)==v['bindings'][str(path)]
 result={}
 for row in json.loads(path.read_text()):
  cid=row['connection_id'];assert cid not in result
  value=struct.unpack('!f',struct.pack('!f',float(row['criticality_float32_text'])))[0]
  assert math.isfinite(value) and 0<=value<=1
  n,d=value.as_integer_ratio();result[cid]=MappingProxyType(dict(row,criticality=value,criticality_numerator=n,criticality_denominator=d))
 assert len(result)==115572
 return MappingProxyType(result),{**v['bindings'],str(proof):sha(proof),str(DIRECTORY/'ablation_protocol_v1.json'):sha(DIRECTORY/'ablation_protocol_v1.json')}
