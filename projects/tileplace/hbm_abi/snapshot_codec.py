"""Explicit little-endian serialization and structural validation for ABI v1."""
import struct
MAGIC=0x434c5054
VERSION=1
FORMATS={
 'blocks':'IIiiiiQQiiiiII','positions':'iiii','sites':'iiiiIIII','regions':'iiiiiiiI',
 'nets':'IIIIQQQQ','net_members':'I','connections':'IIQ','units':'QQIIII',
 'unit_members':'I','prefix_lines':'iiQQQ','prefix_entries':'iIQ','routed_edges':'IIQ','focus':'I'}
RECORDS={name:struct.Struct('<'+fmt) for name,fmt in FORMATS.items()}
HEADER=struct.Struct('<IIQ'+'QQ'*len(FORMATS))

def validate(snapshot):
 arrays={name:snapshot[name] for name in FORMATS}
 def check_range(offset,count,name):
  if offset<0 or count<0 or offset>len(arrays[name]) or count>len(arrays[name])-offset:
   raise ValueError('invalid range into '+name)
 blocks=arrays['blocks'];ids={b[0] for b in blocks}
 if len(ids)!=len(blocks) or len(arrays['positions'])!=len(blocks):raise ValueError('block identity/count mismatch')
 for b in blocks:
  check_range(b[6],b[7],'regions')
  if b[12]&~0x8000000f:raise ValueError('unknown fixed-mask bits')
  if not b[12]&0x80000000 and b[7]:raise ValueError('unrestricted block has regions')
  if b[13]>=len(arrays['units']):raise ValueError('unknown unit')
 for row in arrays['sites']:
  if any(row[5:]):raise ValueError('nonzero site reserved words')
 if len({tuple(s[:4]) for s in arrays['sites']})!=len(arrays['sites']):raise ValueError('duplicate site')
 for r in arrays['regions']:
  if r[7] or r[0]>r[2] or r[1]>r[3] or r[4]>r[5] or r[6]<-1:raise ValueError('invalid region')
 if len({r[0] for r in arrays['nets']})!=len(arrays['nets']):raise ValueError('duplicate net')
 for n in arrays['nets']:
  if any(n[1:4]):raise ValueError('nonzero net reserved words')
  check_range(n[4],n[5],'net_members');check_range(n[6],n[7],'connections')
 for name in ['net_members','unit_members','focus']:
  if any(r[0] not in ids for r in arrays[name]):raise ValueError('unknown block in '+name)
 for name in ['connections','routed_edges']:
  if any(r[0] not in ids or r[1] not in ids for r in arrays[name]):raise ValueError('unknown connection endpoint')
 owners={}
 for index,u in enumerate(arrays['units']):
  check_range(u[0],u[1],'unit_members')
  if u[2] not in (0,1) or any(u[3:]) or not u[1]:raise ValueError('invalid unit')
  for row in arrays['unit_members'][u[0]:u[0]+u[1]]:
   if row[0] in owners:raise ValueError('overlapping unit membership')
   owners[row[0]]=index
 if owners!={b[0]:b[13] for b in blocks}:raise ValueError('unit membership disagrees with blocks')
 keys=set()
 for axis,line,total,offset,count in arrays['prefix_lines']:
  check_range(offset,count,'prefix_entries')
  if axis not in (0,1) or (axis,line) in keys:raise ValueError('invalid prefix line')
  keys.add((axis,line));entries=arrays['prefix_entries'][offset:offset+count]
  if not entries or entries[0][2]!=0:raise ValueError('invalid prefix origin')
  previous=None;last=0
  for coordinate,reserved,cumulative in entries:
   if reserved or (previous is not None and coordinate<=previous) or cumulative<last or cumulative>total:
    raise ValueError('invalid prefix entry')
   previous,last=coordinate,cumulative
 return snapshot

def encode(snapshot):
 validate(snapshot)
 values=[MAGIC,VERSION,snapshot['generation']]
 for name in FORMATS:values.extend([0,len(snapshot[name])])
 return HEADER.pack(*values)+b''.join(RECORDS[name].pack(*row) for name in FORMATS for row in snapshot[name])

def decode(data):
 if len(data)<HEADER.size:raise ValueError('truncated header')
 header=HEADER.unpack_from(data)
 if header[:2]!=(MAGIC,VERSION):raise ValueError('unsupported ABI identity')
 result={'generation':header[2]};offset=HEADER.size
 for index,name in enumerate(FORMATS):
  start,count=header[3+2*index:5+2*index];record=RECORDS[name]
  if start or count>(len(data)-offset)//record.size:raise ValueError('noncanonical or truncated section')
  result[name]=[record.unpack_from(data,offset+i*record.size) for i in range(count)]
  offset+=count*record.size
 if offset!=len(data):raise ValueError('trailing bytes')
 return validate(result)
