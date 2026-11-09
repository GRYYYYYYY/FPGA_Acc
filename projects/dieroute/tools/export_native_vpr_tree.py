"""Extract exact parent/child/switch trees from native VPR branch traces."""
import argparse,csv,hashlib,json,re
from pathlib import Path
NET=re.compile(r'^\s*Net\s+(\d+)\s+\((.*)\)\s*$')
NODE=re.compile(r'^\s*Node:\s*(\d+)\s+(SOURCE|SINK|OPIN|IPIN|CHANX|CHANY)\b.*?\bSwitch:\s*(-?\d+)(?:\s+Net_pin_index:\s*(\d+))?\s*$')
def extract(route):
 trees={};net=None;source=None;previous=None;seen=set();parents={};rows=[];sinks=[]
 def finish():
  if source is not None and sinks:trees[net]=dict(source=source,edges=rows.copy(),sinks=sinks.copy())
 for line in route.read_text().splitlines():
  m=NET.match(line)
  if m:
   finish();net=int(m[1]);source=None;previous=None;seen=set();parents={};rows=[];sinks=[];continue
  m=NODE.match(line)
  if not m:continue
  assert net is not None
  node,kind,switch,pin=int(m[1]),m[2],int(m[3]),m[4]
  if source is None:
   assert kind=='SOURCE';source=node;seen.add(node)
  elif node in seen:
   assert previous is not None and previous[1]=='SINK','repeated node must restart after a terminal'
  else:
   assert previous is not None and previous[1]!='SINK','new branch lacks existing attachment'
   assert kind!='SOURCE' and node not in parents and previous[2]>=0
   parents[node]=previous[0];rows.append((previous[0],node,previous[2]));seen.add(node)
  if kind=='SINK':assert pin is not None and switch==-1;sinks.append((node,int(pin)))
  previous=(node,kind,switch)
 finish();assert trees
 return trees

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('route',type=Path);p.add_argument('output',type=Path);a=p.parse_args();trees=extract(a.route)
 with a.output.open('x',newline='') as f:
  w=csv.writer(f);w.writerow(['net_id','source','parent','child','switch_id'])
  for net,tree in trees.items():
   for parent,child,switch in tree['edges']:w.writerow([net,tree['source'],parent,child,switch])
 print(json.dumps(dict(status='native_tree_parent_child_switch_records_exported',nets=len(trees),sinks=sum(len(t['sinks']) for t in trees.values()),edges=sum(len(t['edges']) for t in trees.values()),route_sha256=hashlib.sha256(a.route.read_bytes()).hexdigest(),tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())))
if __name__=='__main__':main()
