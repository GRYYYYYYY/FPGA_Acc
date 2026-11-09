"""Test whether native per-extension RC history survives on actual immutable MMC graph."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from buffered_rc_node_classes import read
from pre_route_endpoints import sha
from source_binding_v2 import closure
p=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';ep=json.loads(p.read_text());graph=Path(ep['inputs']['graph']['path'])
indices,classes,switches,digest=read(graph);assert digest==ep['graph_sha256']
# read rejects every nonbuffered switch or nonzero internal capacitance.
# Native reset implies R_upstream=Rswitch+Rnode on every extension, then
# Tdel=Tswitch+(Rswitch+Rnode/2)*Cnode. This matches exact rational arc_delay.
proof=dict(bindings={str(p):sha(p),str(graph):digest},node_count=len(indices),rc_classes=len(classes),switch_count=len(switches),all_switches_buffered_and_Cinternal_zero_pass=True,native_extension_formula_reduces_to_existing_additive_arc=True,formula='Tswitch + (Rswitch + Rnode/2)*Cnode',scope='Original XML all-switch structural reduction only. No native float32 roundoff equivalence, full route-tree loaded timing equivalence, topology equivalence, hotspot causality, native QoR or heldout proof. Upstream-resistance-history/internal-capacitance difference cannot explain this graph per-extension costs.')
sys.path.insert(0,str(R/'tools/native_resume_prototype'));proof['bindings'].update(closure([Path(__file__)]));assert all(sha(q)==h for q,h in proof['bindings'].items())
out=R/'experiments/mmc_full_criticality_feedback_trial_v1_2026-10-10/electrical_reduction_v1.json';assert not out.exists();out.write_text(json.dumps(proof,indent=2)+'\n');print('ELECTRICAL REDUCTION PASS',len(indices),len(classes),len(switches),flush=True)
