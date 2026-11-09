"""Attribute native exchange WL changes using exact RRGraphView lengths."""
import csv,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb3_ex5p_two_net_native_validation_v2_20261015'
def main():
 refs={}
 def bind(path):
  path=Path(path);h=hashlib.sha256()
  with path.open('rb') as stream:
   for block in iter(lambda:stream.read(1048576),b''):h.update(block)
  refs[str(path)]=h.hexdigest();return h.hexdigest()
 def load(path):bind(path);return json.loads(Path(path).read_text())
 def members(path):
  bind(path);result={}
  for row in csv.DictReader(Path(path).open()):result.setdefault(int(row['net_id']),set()).update([int(row['parent']),int(row['child'])])
  return result
 interpretation=load(P/'interpretation.json');protocol=load(P/'protocol.json');case=protocol['case'];rr=Path(case['native_case'])/'rr_graph.xml'
 assert bind(rr)==protocol['source_sha256'][str(rr)]
 length={}
 for _,element in ET.iterparse(rr,events=('end',)):
  if element.tag=='node':
   attributes=element.attrib;location=element.find('loc');value=0
   if attributes['type'] in ['CHANX','CHANY'] and attributes.get('direction')!='NONE':
    value=1+int(location.attrib['xhigh'])-int(location.attrib['xlow'])+int(location.attrib['yhigh'])-int(location.attrib['ylow'])
   length[int(attributes['id'])]=value;element.clear()
  elif element.tag=='edge':element.clear()
 outcomes=[]
 for row in interpretation['outcomes']:
  label=row['label'];arm=label.split('_owner')[0]
  before_dir=R/'work/sb3_fixed_feedback_pair_20261015/native_runs'/('ex5p_'+arm+'_0')
  before=members(before_dir/'route.route_trees.csv');after=members(P/label/'route.route_trees.csv')
  validation=load(P/label/'native_validation/validation.json');parent=load(before_dir/'native_validation/validation.json')
  old_total=sum(length[n] for nodes in before.values() for n in nodes);new_total=sum(length[n] for nodes in after.values() for n in nodes)
  assert old_total==parent['total_wirelength'] and new_total==validation['total_wirelength']
  changes=[]
  for net in sorted(after):
   old=sum(length[n] for n in before[net]);new=sum(length[n] for n in after[net])
   if before[net]!=after[net]:changes.append(dict(net=net,role='target' if net==138 else 'displaced',old_native_wirelength=old,new_native_wirelength=new,delta=new-old))
  assert sum(v['delta'] for v in changes)==row['wirelength_delta_from_parent']
  outcomes.append(dict(label=label,parent_total=old_total,candidate_total=new_total,net_changes=changes))
 bind(Path(__file__).resolve())
 report=dict(status='three_native_exchange_wirelength_changes_exactly_decomposed_by_net',outcomes=outcomes,source_sha256=refs,
  adopted=False,research_complete=False,scope='DirectionNONE=0 and otherCHANX/CHANY=1+dx+dy per unique net node, exact full-design native WL checks. Descriptive attribution, no CPD causal decomposition or new routing.')
 with (P/'wirelength_decomposition.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
 print(json.dumps(dict(status=report['status'],outcomes=outcomes)))
if __name__=='__main__':main()
