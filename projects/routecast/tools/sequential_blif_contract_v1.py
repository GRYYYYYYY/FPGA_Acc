"""Pure sequential BLIF fragment export, retaining clock polarity and ordinary FF initialization."""
def emit(module):
 initial={}
 for net in module['netnames'].values():
  value=net.get('attributes',{}).get('init')
  if value is None:continue
  assert len(value)==len(net['bits'])
  for bit,state in zip(net['bits'],reversed(value)):
   assert state in '01x'
   if state=='x':continue
   assert type(bit)==int
   if bit in initial:assert initial[bit]==state,'conflicting init aliases'
   initial[bit]=state
 def wire(bit):
  assert type(bit)==int or bit in ('0','1')
  return 'b'+str(bit) if type(bit)==int else 'const'+bit
 lines=[];records=[];seen=set()
 for cell_id,cell in module['cells'].items():
  kind=cell['type']
  if not kind.startswith('$_DFF'):continue
  assert kind in ('$_DFF_P_','$_DFF_N_','$_DFF_PP0_','$_DFF_PP1_'),'unsupported sequential type '+kind
  ports=cell['connections'];assert all(len(bits)==1 for bits in ports.values());q=ports['Q'][0];assert q not in seen;seen.add(q);names={p:wire(bits[0]) for p,bits in ports.items()}
  init=initial.get(q,'2')
  if kind in ('$_DFF_P_','$_DFF_N_'):
   assert set(ports)=={'C','D','Q'};edge='re' if kind=='$_DFF_P_' else 'fe';line=f".latch {names['D']} {names['Q']} {edge} {names['C']} {init}"
  else:
   assert set(ports)=={'C','D','Q','R'}
   assert q not in initial,'defined async initial state needs explicit supported model encoding'
   line='.subckt '+kind+' '+' '.join(p+'='+names[p] for p in sorted(names))
  lines.append(line);records.append(dict(cell=cell_id,type=kind,ports=names,init=init))
 assert set(initial)<=seen,'initialized wire not a supported FF output'
 return lines,records
