from pathlib import Path
import hashlib
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from pre_route_endpoints import extract, PhysicalMapContext, sha
from align_endpoint_labels import align
FIXTURE=Path(__file__).parent/'fixtures'


class EndpointTests(unittest.TestCase):
    def test_prepared_maps_exact_and_reject_changed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            net, place = self.prepare(tmp)
            graph = Path(tmp)/'graph.xml'
            graph.write_bytes((FIXTURE/'pre_route_rr.xml').read_bytes())
            context = PhysicalMapContext(graph)
            self.assertEqual(extract(net, place, graph),
                             extract(net, place, graph, physical_context=context))
            maps = context.maps(sha(graph))
            with self.assertRaises(TypeError):
                maps[1][(1, 1, 0)] = None
            with self.assertRaises(TypeError):
                next(iter(maps[0].values()))['pins']['bad'] = None
            graph.write_text(graph.read_text()+'\n')
            with self.assertRaisesRegex(ValueError, 'graph mismatch'):
                extract(net, place, graph, physical_context=context)
            with self.assertRaisesRegex(ValueError, 'invalid physical mapping context'):
                extract(net, place, graph, physical_context=object())

    def prepare(self,tmp,net_text=None):
        net=Path(tmp)/'test.net';place=Path(tmp)/'test.place'
        net.write_text(net_text or (FIXTURE/'pre_route.net').read_text())
        digest=hashlib.sha256(net.read_bytes()).hexdigest()
        place.write_text(f'Netlist_File: test.net Netlist_ID: SHA256:{digest}\nArray size: 3 x 3 logic blocks\n'
                         'cluster_name 1 1 0 0 #0\nout:external_name 2 1 1 0 #1\n')
        return net,place

    def test_reference_trace_subtile_and_tall_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            net,place=self.prepare(tmp)
            result,report=extract(net,place,FIXTURE/'pre_route_rr.xml')
            self.assertEqual(result['connections'],[{'connection_id':0,'net_id':0,'source':10,'sink':50}])
            self.assertEqual(result['net_names'],{'0':'external_name'})
            self.assertEqual([p['class_id'] for p in report['pin_details']],[1,2])
            self.assertNotIn('route',result['inputs'])

    def test_class_bbox_inside_tall_tile(self):
        with tempfile.TemporaryDirectory() as tmp:
            net,place=self.prepare(tmp)
            text=(FIXTURE/'pre_route_rr.xml').read_text().replace('<grid>','<grid>\n<grid_loc x="1" y="2" layer="0" block_type_id="1" width_offset="0" height_offset="1"/>').replace('ylow="1" yhigh="2"','ylow="2" yhigh="2"')
            graph=Path(tmp)/'inside.xml';graph.write_text(text)
            result,_=extract(net,place,graph)
            self.assertEqual(result['connections'][0]['source'],10)
            bad=text.replace('ylow="2" yhigh="2"','ylow="2" yhigh="3"');graph.write_text(bad)
            with self.assertRaisesRegex(ValueError,'crosses physical tile'):extract(net,place,graph)

    def test_reject_netlist_identity_and_illegal_subtile(self):
        with tempfile.TemporaryDirectory() as tmp:
            net,place=self.prepare(tmp);net.write_text(net.read_text()+'\n')
            with self.assertRaisesRegex(ValueError,'identity'):extract(net,place,FIXTURE/'pre_route_rr.xml')
            net,place=self.prepare(tmp);place.write_text(place.read_text().replace('2 1 1 0 #1','2 1 2 0 #1'))
            with self.assertRaisesRegex(ValueError,'mapping'):extract(net,place,FIXTURE/'pre_route_rr.xml')

    def test_reject_reference_cycle_and_unresolved_child(self):
        text=(FIXTURE/'pre_route.net').read_text()
        variants=[text.replace('child[0].out[0]-&gt;output_mux','unknown[0].out[0]-&gt;output_mux'),
                  text.replace('<port name="out">external_name</port>','<port name="out">core.O[0]-&gt;cycle</port>')]
        with tempfile.TemporaryDirectory() as tmp:
            for variant in variants:
                net,place=self.prepare(tmp,variant)
                with self.assertRaises(ValueError):extract(net,place,FIXTURE/'pre_route_rr.xml')

    def test_clock_policy_exclusion_is_explicit(self):
        text=(FIXTURE/'pre_route.net').read_text().replace('<clocks/>','<clocks>external_name</clocks>',1)
        with tempfile.TemporaryDirectory() as tmp:
            net,place=self.prepare(tmp,text);result,_=extract(net,place,FIXTURE/'pre_route_rr.xml')
            self.assertEqual(result['connections'],[])
            self.assertEqual(result['excluded_nets'][0]['reason'],'explicit exclude_root_clocks policy')
            with self.assertRaises(ValueError):extract(net,place,FIXTURE/'pre_route_rr.xml','guess')

    def test_label_join_preserves_duplicate_endpoint_multiplicity(self):
        endpoints={'graph_sha256':'x','connections':[{'connection_id':9,'net_id':2,'source':3,'sink':4},
                                                  {'connection_id':10,'net_id':2,'source':3,'sink':4}]}
        labels={'graph_sha256':'x','connections':[{'connection_id':1,'net_id':2,'source':3,'sink':4,'edge_ids':[0]},
                                               {'connection_id':0,'net_id':2,'source':3,'sink':4,'edge_ids':[1]}]}
        result=align(endpoints,labels)
        self.assertEqual([r['connection_id'] for r in result['connections']],[9,10])
        self.assertEqual([r['edge_ids'] for r in result['connections']],[[0],[1]])
        with self.assertRaises(ValueError):align({**endpoints,'connections':endpoints['connections'][:1]},labels)


if __name__=='__main__':unittest.main()
