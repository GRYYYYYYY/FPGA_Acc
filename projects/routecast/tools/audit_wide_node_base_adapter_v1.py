"""Return exact wide node costs only after independent original-XML bit audit."""
import json
import struct
from pathlib import Path
from audit_structural_node_base_wide_v1 import audit as independent_audit
from pre_route_endpoints import sha

def audit(graph,proof_path,scale):
    graph=Path(graph).resolve();proof_path=Path(proof_path).resolve()
    v=json.loads(proof_path.read_text())
    assert v['scale']==scale and v['bindings'][str(graph)]==sha(graph)
    result=independent_audit(proof_path)
    assert result['all_pass'] and result['independent_XML_float32_bits_and_payload_all_entries_equal']
    path=proof_path.parent/v['payload_file']
    values=tuple(lo+(hi<<64) for lo,hi in struct.iter_unpack('<QQ',path.read_bytes()))
    assert len(values)==v['nodes'] and sha(path)==v['bindings'][str(path)]
    return values
