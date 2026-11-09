"""Authenticated partial route plus target global-block metadata, exclusive publication.

Same packed NET graph/identity is a caller prerequisite. Serial input writers only;
publication is atomic, not a concurrent multi-file placement transaction.
"""
import json,os,re,tempfile
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
HEADER=re.compile(r'^Net\s+\d+\s+\((.*)\)(?:\s*:.*)?\s*$')
BLOCK=re.compile(r'^Block (\S+) \(#(\d+)\) at \((\d+),(\d+),(\d+)\)')
def publish_partial_seed(seed,place,endpoint,excluded,destination):
 seed,place,endpoint,destination=map(Path,(seed,place,endpoint,destination))
 if destination.exists():raise FileExistsError(destination)
 before={str(f):sha(f) for f in (seed,place,endpoint)};meta=json.loads(endpoint.read_text())
 if not all(sha(v['path'])==v['sha256'] for v in meta['inputs'].values()):raise ValueError('endpoint input changed')
 if sha(place)!=meta['inputs']['place']['sha256']:raise ValueError('target placement binding')
 locations={};ids=set()
 for row in place.read_text().splitlines():
  parts=row.split()
  if not row or row.startswith('#') or len(parts)!=6 or not parts[5].startswith('#'):continue
  name=parts[0];number=int(parts[5][1:]);loc=(int(parts[1]),int(parts[2]),int(parts[4]))
  if name in locations or number in ids:raise ValueError('duplicate placement block')
  locations[name]=(number,loc);ids.add(number)
 if not locations:raise ValueError('empty placement block table')
 old=physical_paths(seed);excluded=set(excluded);lines=seed.read_text().splitlines(keepends=True)
 if not lines or not lines[0].startswith('Placement_File:'):raise ValueError('route header')
 lines[0]=f'Placement_File: design.place Placement_ID: SHA256:{before[str(place)]}\n';output=[];keep=True;changes=[];checked=0
 for line in lines:
  net=HEADER.match(line)
  if line.startswith('Net ') and net is None:raise ValueError('unparsed NET header')
  if net:keep=net[1] not in excluded
  if not keep:continue
  block=BLOCK.match(line)
  if line.startswith('Block ') and block is None:raise ValueError('unparsed global block')
  if block:
   block_name=block[1]
   if block_name not in locations:raise ValueError('global block missing from placement')
   number,loc=locations[block_name]
   if number!=int(block[2]):raise ValueError('global block identity mismatch')
   previous=tuple(map(int,block.group(3,4,5)));checked+=1
   if previous!=loc:changes.append(dict(block=block_name,block_id=number,old=previous,new=loc))
   line=re.sub(r'at \([^)]*\)',f'at ({loc[0]},{loc[1]},{loc[2]})',line,count=1)
  output.append(line)
 stage=None
 try:
  with tempfile.NamedTemporaryFile(mode='w',dir=destination.parent,prefix='.partial_seed_',delete=False) as stream:
   stage=Path(stream.name);stream.write(''.join(output));stream.flush();os.fsync(stream.fileno())
  actual=physical_paths(stage);norm=lambda ps:{n:Counter(paths) for n,paths in ps.items() if paths}
  if norm(actual)!={n:Counter(paths) for n,paths in old.items() if paths and n not in excluded}:raise ValueError('retained physical paths changed')
  observed=Counter((name,path[0][0],path[-1][0]) for name,paths in actual.items() for path in paths)
  expected=Counter((meta['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in meta['connections'] if meta['net_names'][str(q['net_id'])] not in excluded)
  if observed!=expected:raise ValueError('retained target endpoints mismatch')
  if not all(sha(f)==h for f,h in before.items()) or not all(sha(v['path'])==v['sha256'] for v in meta['inputs'].values()):raise ValueError('inputs changed during update')
  # Hard-link publication is atomic and fails if another writer created destination.
  digest=sha(stage);os.link(stage,destination)
  return dict(input_hashes=before,output_sha256=digest,retained_connections=sum(observed.values()),checked_global_blocks=checked,global_block_coordinate_changes=changes,physical_paths_exact=True,scope='Serial same-packed-net placement state adapter; final native FULL/STA required. Atomic exclusive artifact publication, not concurrent epoch service.')
 finally:
  if stage is not None:stage.unlink(missing_ok=True)
