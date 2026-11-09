"""Canonical ABI entry point, retaining the historical structural codec separately."""
import snapshot_codec as legacy

def validate(snapshot):
 legacy.validate(snapshot)
 def ordered(values):
  if any(a>=b for a,b in zip(values,values[1:])):raise ValueError('noncanonical ordering')
 for name in ['blocks','nets','focus']:ordered([row[0] for row in snapshot[name]])
 ordered([tuple(row[:4]) for row in snapshot['sites']])
 ordered([tuple(row[:2]) for row in snapshot['routed_edges']])
 ordered([tuple(row[:2]) for row in snapshot['prefix_lines']])
 for owner,target,field in [('blocks','regions',6),('nets','net_members',4),('nets','connections',6),('units','unit_members',0),('prefix_lines','prefix_entries',3)]:
  cursor=0
  for row in snapshot[owner]:
   offset,count=row[field:field+2]
   if offset!=cursor:raise ValueError('noncanonical CSR partition')
   cursor+=count
  if cursor!=len(snapshot[target]):raise ValueError('unreferenced CSR records')
 blocks={b[0]:b for b in snapshot['blocks']};sites={tuple(row[:4]):row[4] for row in snapshot['sites']}
 for b in blocks.values():
  if any(not b[12]&(1<<i) and b[8+i] for i in range(4)):raise ValueError('unused fixed coordinate')
 for net in snapshot['nets']:
  members=[row[0] for row in snapshot['net_members'][net[4]:net[4]+net[5]]];ordered(members)
  members=set(members)
  for row in snapshot['connections'][net[6]:net[6]+net[7]]:
   if row[0] not in members or row[1] not in members:raise ValueError('connection outside network')
 for row in snapshot['routed_edges']:
  if row[0]>=row[1] or row[2]<=0:raise ValueError('invalid routed feedback')
 for unit in snapshot['units']:
  members=[row[0] for row in snapshot['unit_members'][unit[0]:unit[0]+unit[1]]];ordered(members)
  if not unit[2] and any(blocks[id][12]&15 for id in members):raise ValueError('fixed block in movable unit')
 def placement_valid(positions):
  if len(set(positions.values()))!=len(positions):raise ValueError('placement collision')
  for id,p in positions.items():
   b=blocks[id]
   if sites.get(p)!=b[1]:raise ValueError('placement site/type mismatch')
   if any(b[12]&(1<<i) and p[i]!=b[8+i] for i in range(4)):raise ValueError('fixed location mismatch')
   if b[12]&0x80000000:
    regions=snapshot['regions'][b[6]:b[6]+b[7]]
    if not any(r[0]<=p[0]<=r[2] and r[1]<=p[1]<=r[3] and r[4]<=p[3]<=r[5] and (r[6]==-1 or r[6]==p[2]) for r in regions):raise ValueError('region restriction mismatch')
  for unit in snapshot['units']:
   ids=[row[0] for row in snapshot['unit_members'][unit[0]:unit[0]+unit[1]]]
   root=ids[0]
   for id in ids:
    if any(positions[id][j]-positions[root][j]!=blocks[id][2+j]-blocks[root][2+j] for j in range(4)):raise ValueError('macro shape mismatch')
 placement_valid({id:tuple(b[2:6]) for id,b in blocks.items()})
 placement_valid({b[0]:tuple(p) for b,p in zip(snapshot['blocks'],snapshot['positions'])})
 return snapshot

def encode(snapshot):validate(snapshot);return legacy.encode(snapshot)
def decode(data):return validate(legacy.decode(data))
