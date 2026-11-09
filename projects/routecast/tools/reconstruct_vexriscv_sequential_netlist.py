"""Restore exact state records around authenticated LUT-mapped logic."""
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha


def logical_lines(path):
    pending = ''
    for line in path.read_text().splitlines():
        line = pending + line.strip()
        if line.endswith('\\'):
            pending = line[:-1] + ' '
        else:
            yield line
            pending = ''
    assert not pending


def main():
    root = Path(__file__).resolve().parents[1]
    src = root / 'experiments/vexriscv_combinational_cut_mapping_2026-10-06'
    receipt = json.loads((src / 'receipt.json').read_text())
    assert sha(src / 'protocol.json') == receipt['protocol_sha256']
    assert all(sha(src/name) == h for name,h in receipt['artifacts'].items())
    flat = list(logical_lines(src / 'flat.blif'))
    mapped = list(logical_lines(src / 'mapped_cut.blif'))
    state = json.loads((src / 'sequential_records.json').read_text())
    assert state == [s for s in flat if s.startswith(('.latch ', '.subckt '))]
    original_inputs = next(s for s in flat if s.startswith('.inputs '))
    original_outputs = next(s for s in flat if s.startswith('.outputs '))
    body = [s for s in mapped if not s.startswith(('.model ','.inputs ','.outputs ','.end'))]
    drivers = original_inputs.split()[1:] + [s.split()[-1] for s in body if s.startswith('.names ')]
    uses = original_outputs.split()[1:]
    for s in body:
        if s.startswith('.names '): uses.extend(s.split()[1:-1])
    async_types = {}
    for s in state:
        tokens = s.split()
        if tokens[0] == '.latch':
            uses.extend([tokens[1],tokens[4]]); drivers.append(tokens[2])
        else:
            pins = dict(t.split('=',1) for t in tokens[2:])
            drivers.append(pins['Q']); uses.extend(pins[k] for k in ('D','C','R'))
            async_types[tokens[1]] = async_types.get(tokens[1],0)+1
    assert len(drivers) == len(set(drivers)), 'duplicate drivers'
    missing = sorted(set(uses)-set(drivers))
    assert not missing, missing
    architecture = root.parent / 'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/arch/COFFE_22nm/k6FracN10LB_mem20K_complexDSP_customSB_22nm.xml'
    arch = ET.parse(architecture).getroot()
    models = {m.attrib['name'] for m in arch.findall('./models/model')}
    supported = set(models)
    for pb in arch.iter('pb_type'):
        model = pb.get('blif_model','')
        if model.startswith('.subckt '): supported.add(model.split()[1])
    unsupported = sorted(set(async_types)-supported)
    out = root / 'experiments/vexriscv_sequential_reconstruction_2026-10-06'
    out.mkdir()
    shutil.copyfile(__file__,out/'source.py')
    netlist = '\n'.join(['.model VexRiscvSmallest',original_inputs,original_outputs,*body,*state,'.end'])+'\n'
    (out/'design.blif').write_text(netlist)
    protocol = {'mapping_receipt_sha256':sha(src/'receipt.json'),'architecture_path':str(architecture),
                'architecture_sha256':sha(architecture),'source_sha256':sha(__file__),
                'scope':'restore original primary ports and every exact sequential record around CEC-verified LUT logic; architecture model audit only'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    result = {'protocol_sha256':sha(out/'protocol.json'),'design_sha256':sha(out/'design.blif'),
              'primary_ports_preserved':True,'sequential_records_exact':True,'state_records':len(state),
              'single_driver_and_all_uses_driven':True,'async_cell_counts':async_types,
              'unsupported_async_models':unsupported,'vpr_ready':not unsupported,
              'routing_executed':False,'unseen_family_claim':False,
              'limitation':'no whole HDL equivalence or asynchronous model timing proof; existing architecture unmodified'}
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
