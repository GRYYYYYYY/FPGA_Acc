#!/usr/bin/env python3
"""Hand-specified used-site connectivity, including adversarial mutations."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_native_timing_pins import SiteConnectivity
from audit_native_load_slacks import checked_query, checked_bindings
from analyze_native_delay_paths import path_depth


def pin(wire, bel, name, direction, kind, cell='', logical='', route=False):
    return dict(net_id='7',site_inst='S',site='S',wire=wire,bel=bel,pin=name,
                direction=direction,bel_class=kind,site_port=str(kind=='PORT').lower(),
                cell=cell,cell_type='LUT' if cell else '',logical_pin=logical,routethru=str(route).lower())


def mux(bel, wi, wo):
    return dict(net_id='7',site_inst='S',bel=bel,input_pin='I',output_pin='O',input_wire=wi,output_wire=wo)


def fixture():
    wires=[pin('entry','A1','A1','OUTPUT','PORT'),
           pin('entry','MUX','I','INPUT','RBEL'),pin('exit','MUX','O','OUTPUT','RBEL'),
           pin('exit','FF','D','INPUT','BEL','load','D')]
    return wires,[mux('MUX','entry','exit')]


class SiteTraceTest(unittest.TestCase):
    def test_net_segment_aliases_preserve_membership(self):
        loads=[dict(net_id='7',to_pin='load/D',net_name='root')]
        bindings=[dict(net_id='7',to_pin='load/D',requested_net='root',direct_net='child/wire',segment_count='2')]
        segments=[dict(net_id='7',to_pin='load/D',segment=n) for n in ('root','child/wire')]
        self.assertEqual(checked_bindings(loads,bindings,segments),1)
        for bad in [segments[:1],segments+segments[:1],segments[:1]+[dict(segments[1],segment='unrelated')]]:
            with self.assertRaises(AssertionError):checked_bindings(loads,bindings,bad)
        with self.assertRaises(AssertionError):checked_bindings(loads,bindings+bindings,segments)

    def test_missing_timing_path_is_not_a_slack(self):
        status=dict(net_id='7',to_pin='load/D',kind='min',status='no_reported_path',object_count='0')
        self.assertIsNone(checked_query(status,{}))
        with self.assertRaises(AssertionError):
            checked_query(status,{'SLACK':'0'})
        status['status']='unresolved'
        with self.assertRaises(AssertionError):
            checked_query(status,{})

    def test_constrained_path_properties_and_finite_slack(self):
        status=dict(net_id='7',to_pin='load/D',kind='min',status='resolved',object_count='1')
        props=dict(CLASS='timing_path',DELAY_TYPE='min',STARTPOINT_PIN='src/C',ENDPOINT_PIN='load/D',CORNER='Slow')
        props.update({k:'0.100' for k in ('SLACK','DATAPATH_DELAY','DATAPATH_LOGIC_DELAY','DATAPATH_NET_DELAY',
                      'REQUIREMENT','REQUIRED_TIME','STARTPOINT_CLOCK_DELAY','ENDPOINT_CLOCK_DELAY')})
        self.assertEqual(checked_query(status,props),dict(props,_classification='constrained_path'))
        for key,value in [('SLACK','NaN'),('DELAY_TYPE','max'),('CLASS','net_delay'),('CORNER','NA')]:
            bad=dict(props);bad[key]=value
            with self.subTest(key=key),self.assertRaises((AssertionError,ValueError)):
                checked_query(status,bad)
        unconstrained=dict(props,SLACK='',REQUIREMENT='',REQUIRED_TIME='')
        self.assertEqual(checked_query(status,unconstrained)['_classification'],'reported_unconstrained_path')
        with self.assertRaises(AssertionError):
            checked_query(status,dict(unconstrained,REQUIRED_TIME='1.0'))

    def test_existing_path_depth_rejects_cycle_and_disconnect(self):
        self.assertEqual(path_depth(0,3,{3:2,2:1,1:0}),3)
        for parents in [{3:2,2:3},{3:2}]:
            with self.assertRaises(AssertionError):path_depth(0,3,parents)

    def test_enabled_mux_and_shared_sink(self):
        wires,pips=fixture();wires.append(pin('exit','FF2','D','INPUT','BEL','load2','D'))
        graph=SiteConnectivity(wires,pips)
        kind,terminal,proof=graph.trace(7,'S','exit')
        self.assertEqual((kind,terminal),('site_input','A1'))
        self.assertEqual([r['wire'] for r in proof],['exit','entry'])

    def test_intrasite_source(self):
        wires,pips=fixture();wires[0]=pin('entry','LUT','O','OUTPUT','BEL','source','O')
        kind,terminal,proof=SiteConnectivity(wires,pips).trace(7,'S','exit')
        self.assertEqual((kind,terminal),('internal_driver',('source','O')))

    def test_unselected_mux(self):
        wires,_=fixture()
        with self.assertRaisesRegex(AssertionError,'unselected'):
            SiteConnectivity(wires,[]).trace(7,'S','exit')

    def test_conflicting_mux_settings(self):
        wires,pips=fixture()
        with self.assertRaisesRegex(AssertionError,'multiple enabled'):
            SiteConnectivity(wires,pips+pips)

    def test_wrong_net_or_wire_rejected(self):
        wires,pips=fixture()
        for key,value in [('net_id','8'),('input_wire','other'),('output_wire','other')]:
            altered=copy.deepcopy(pips);altered[0][key]=value
            with self.subTest(key=key),self.assertRaises((AssertionError,KeyError)):
                SiteConnectivity(wires,altered)

    def test_cycle(self):
        wires,pips=fixture();wires[0]=pin('entry','MUX2','O','OUTPUT','RBEL')
        wires.append(pin('exit','MUX2','I','INPUT','RBEL'));pips.append(mux('MUX2','exit','entry'))
        with self.assertRaisesRegex(AssertionError,'cycle'):
            SiteConnectivity(wires,pips).trace(7,'S','exit')

    def test_missing_and_ambiguous_driver(self):
        wires,pips=fixture()
        for changed in [wires[1:],wires+[pin('entry','B1','B1','OUTPUT','PORT')]]:
            with self.assertRaisesRegex(AssertionError,'driver'):
                SiteConnectivity(changed,pips).trace(7,'S','exit')

    def test_unsupported_route_through_or_unmapped_driver(self):
        wires,pips=fixture()
        for driver in [pin('entry','LUT','O','OUTPUT','BEL','source','O',True),
                       pin('entry','LUT','O','OUTPUT','BEL','source','')]:
            changed=copy.deepcopy(wires);changed[0]=driver
            with self.assertRaisesRegex(AssertionError,'unsupported internal driver'):
                SiteConnectivity(changed,pips).trace(7,'S','exit')

    def test_duplicate_pin_and_unsupported_direction(self):
        wires,pips=fixture()
        with self.assertRaisesRegex(AssertionError,'duplicate'):
            SiteConnectivity(wires+wires[:1],pips)
        wires[0]['direction']='INOUT'
        with self.assertRaisesRegex(AssertionError,'bidirectional'):
            SiteConnectivity(wires,pips)


if __name__=='__main__':
    unittest.main()
