import tempfile,unittest
from pathlib import Path
from blif_undriven_outputs import undriven_outputs
ARCH='''<architecture><models><model name="comb"><input_ports><port name="a" combinational_sink_ports="y"/><port name="other" combinational_sink_ports="z"/></input_ports><output_ports><port name="y"/><port name="z"/><port name="q" clock="clk"/><port name="clockout" is_clock="1"/></output_ports></model></models></architecture>'''
class UndrivenTests(unittest.TestCase):
 def run_case(self,text,arch=ARCH):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a.xml';b=Path(d)/'b.blif';a.write_text(arch);b.write_text(text);return undriven_outputs(b,a)
 def test_semantic_ports_not_names(self):
  r=self.run_case('.subckt comb y=arbitrary other=connected z=driven q=seq clockout=osc\n.subckt comb a=signal y=~GND\n')
  self.assertEqual(set(r),{'arbitrary'});self.assertIsNone(r['arbitrary']['constant_value'])
 def test_bus_continuation_and_omitted_inputs(self):
  r=self.run_case('.subckt comb \\\n y[0]=n0 y[1]=n1\n.subckt comb a[0]=open y=still_driven\n.subckt unknown y=unknown\n')
  self.assertEqual(set(r),{'n0','n1'})
 def test_bad_metadata_assignments(self):
  for text in ('.subckt comb y=n y=n2','.subckt comb nope=n','.subckt comb y=n\n.subckt comb y=n','.subckt comb y=n \\'):
   with self.assertRaises(ValueError):self.run_case(text)
  with self.assertRaises(ValueError):self.run_case('.subckt comb y=n',ARCH.replace('sink_ports="y"','sink_ports="missing"'))
