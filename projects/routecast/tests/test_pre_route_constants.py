import hashlib,tempfile,unittest
from pathlib import Path
import test_pre_route_endpoints as fixture
from pre_route_constants import extract_with_constants

class ConstantPolicyTests(unittest.TestCase):
    def test_policy_and_atom_identity(self):
        with tempfile.TemporaryDirectory() as d:
            atom=Path(d)/'test.blif';atom.write_text('.names external_name\n')
            text=(fixture.FIXTURE/'pre_route.net').read_text().replace('<block ', '<block atom_netlist_id="SHA256:'+hashlib.sha256(atom.read_bytes()).hexdigest()+'" ',1)
            net,place=fixture.EndpointTests().prepare(d,text)
            routed,_=extract_with_constants(net,place,fixture.FIXTURE/'pre_route_rr.xml',atom,'route')
            global_result,_=extract_with_constants(net,place,fixture.FIXTURE/'pre_route_rr.xml',atom,'global')
            self.assertEqual(len(routed['connections']),1);self.assertEqual(global_result['connections'],[])
            self.assertEqual(global_result['excluded_nets'][0]['constant_value'],0)
            atom.write_text('.names external_name\n1\n')
            with self.assertRaisesRegex(ValueError,'identity'):extract_with_constants(net,place,fixture.FIXTURE/'pre_route_rr.xml',atom,'global')

    def test_architecture_global_vs_route(self):
        with tempfile.TemporaryDirectory() as d:
            atom=Path(d)/'test.blif';atom.write_text('.subckt comb y=external_name\n')
            arch=Path(d)/'a.xml';arch.write_text('<architecture><models><model name="comb"><input_ports><port name="a" combinational_sink_ports="y"/></input_ports><output_ports><port name="y"/></output_ports></model></models></architecture>')
            text=(fixture.FIXTURE/'pre_route.net').read_text().replace('<block ', '<block atom_netlist_id="SHA256:'+hashlib.sha256(atom.read_bytes()).hexdigest()+'" ',1)
            net,place=fixture.EndpointTests().prepare(d,text)
            legacy,_=extract_with_constants(net,place,fixture.FIXTURE/'pre_route_rr.xml',atom,'global')
            routed,_=extract_with_constants(net,place,fixture.FIXTURE/'pre_route_rr.xml',atom,'route',arch)
            global_result,report=extract_with_constants(net,place,fixture.FIXTURE/'pre_route_rr.xml',atom,'global',arch)
            self.assertEqual(len(legacy['connections']),1);self.assertEqual(len(routed['connections']),1);self.assertEqual(global_result['connections'],[])
            self.assertIsNone(global_result['excluded_nets'][0]['constant_value']);self.assertEqual(report['undriven_outputs']['external_name']['model'],'comb')

if __name__=='__main__':unittest.main()
