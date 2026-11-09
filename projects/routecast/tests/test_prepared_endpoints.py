from pathlib import Path
import tempfile,unittest,hashlib
import test_pre_route_endpoints as fixture
from pre_route_endpoints import extract
from prepared_endpoints import PreparedEndpoints
from pre_route_constants import extract_with_constants

class PreparedEndpointTests(unittest.TestCase):
    def test_repeat_and_changed_subtile_match_fresh_oracle(self):
        with tempfile.TemporaryDirectory() as d:
            net,place=fixture.EndpointTests().prepare(d);graph=Path(d)/'graph.xml'
            text=(fixture.FIXTURE/'pre_route_rr.xml').read_text().replace('<node id="50"','<node id="51" type="SINK" capacity="1"><loc xlow="2" xhigh="2" ylow="1" yhigh="1" layer="0" ptc="0"/></node>\n<node id="50"');graph.write_text(text)
            prepared=PreparedEndpoints(net,graph,place)
            first,report=prepared.project(place);first['connections'].clear()
            report['excluded_nets'].append({'net_id':0});report['pin_details'][0]['net_id']=99
            self.assertEqual(prepared.project(place)[0]['connections'],extract(net,place,graph)[0]['connections'])
            place.write_text(place.read_text().replace('2 1 1 0 #1','2 1 0 0 #1'))
            actual,_=prepared.project(place);expected,_=extract(net,place,graph)
            self.assertEqual(actual['connections'],expected['connections']);self.assertEqual(actual['connections'][0]['sink'],51)
    def test_invalid_mapping_and_static_change_do_not_mutate_state(self):
        with tempfile.TemporaryDirectory() as d:
            net,place=fixture.EndpointTests().prepare(d);graph=Path(d)/'graph.xml';graph.write_text((fixture.FIXTURE/'pre_route_rr.xml').read_text());prepared=PreparedEndpoints(net,graph,place)
            original=place.read_text();place.write_text(original.replace('2 1 1 0 #1','2 1 2 0 #1'))
            with self.assertRaises(ValueError):prepared.project(place)
            place.write_text(original);self.assertEqual(len(prepared.project(place)[0]['connections']),1)
            graph.write_text(graph.read_text()+'\n')
            with self.assertRaisesRegex(ValueError,'identity'):prepared.project(place)
    def test_constant_exclusion_preserves_connection_id_gaps(self):
        with tempfile.TemporaryDirectory() as d:
            atom=Path(d)/'test.blif';atom.write_text('.names external_name\n.names x unknown_var\n1 1\n')
            text=(fixture.FIXTURE/'pre_route.net').read_text().replace('<block ', '<block atom_netlist_id="SHA256:'+hashlib.sha256(atom.read_bytes()).hexdigest()+'" ',1)
            text=text.replace('<inputs><port name="pad">external_name</port></inputs><outputs/>','<inputs><port name="pad">external_name</port></inputs><outputs><port name="out">unknown_var</port></outputs>')
            prefix,suffix=text.rsplit('</block>',1)
            text=prefix+'<block name="out:unknown_var" instance="io[10]"><inputs><port name="pad">unknown_var</port></inputs><outputs/><clocks/></block></block>'+suffix
            net,place=fixture.EndpointTests().prepare(d,text);place.write_text(place.read_text()+'out:unknown_var 2 1 0 0 #2\n')
            graph=Path(d)/'graph.xml';xml=(fixture.FIXTURE/'pre_route_rr.xml').read_text()
            extra='<node id="51" type="SINK" capacity="1"><loc xlow="2" xhigh="2" ylow="1" yhigh="1" layer="0" ptc="0"/></node><node id="60" type="SOURCE" capacity="1"><loc xlow="2" xhigh="2" ylow="1" yhigh="1" layer="0" ptc="3"/></node>'
            graph.write_text(xml.replace('</rr_nodes>',extra+'</rr_nodes>'))
            prepared=PreparedEndpoints(net,graph,place,atom=atom,constant_net_method='global')
            actual,_=prepared.project(place);expected,_=extract_with_constants(net,place,graph,atom,'global')
            self.assertEqual(actual['connections'],expected['connections']);self.assertEqual(actual['connections'][0]['connection_id'],1)

    def test_constant_policy_pair_required(self):
        with self.assertRaises(ValueError):PreparedEndpoints('missing','missing','missing',atom='missing')

if __name__=='__main__':unittest.main()
