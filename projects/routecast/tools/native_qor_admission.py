"""Authenticated raw FULL/STA screening before expensive canonical publication.

Admission is provisional: a candidate must still pass zero-fixup canonical
reload and path/ledger preservation. Rejected candidates require no publication.
"""
import re
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha

def joint_qor(candidate_cpd,candidate_wire,cold_cpd,cold_wire):
 a,b=Fraction(candidate_cpd),Fraction(cold_cpd)
 if a<0 or b<0 or any(type(x) is not int or x<0 for x in [candidate_wire,cold_wire]):raise ValueError('invalid QoR')
 reasons=[]
 if a>b:reasons.append('CPD_REGRESSION')
 if candidate_wire>cold_wire:reasons.append('WIRELENGTH_REGRESSION')
 return dict(admitted=not reasons,reasons=reasons)

def file_named(row,name):
 paths=[Path(f) for f in row['files'] if Path(f).name==name]
 if len(paths)!=1:raise ValueError('ambiguous/missing '+name)
 return paths[0]

def bind(row):
 if not all(sha(f)==d for f,d in row['files'].items()):raise ValueError('artifact identity changed')

def qos(log):
 text=Path(log).read_text()
 if 'VPR succeeded' not in text or 'Completed routing consistency check successfully.' not in text:raise ValueError('native FULL/STA evidence missing')
 cpds=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text);wires=re.findall(r'Total wirelength:\s*(\d+)',text)
 if not cpds or not wires:raise ValueError('native QoR missing')
 return cpds[-1],int(wires[-1])

def admit(cold,raw):
 if cold['count']!=raw['count']:raise ValueError('case mismatch')
 bind(cold)
 if cold['exit_code']!=0 or cold['timed_out']:raise ValueError('cold reference failed')
 cpd,wire=qos(file_named(cold,'cold.log'))
 if Fraction(cpd)!=Fraction(cold['cpd_ns']) or wire!=cold['wirelength']:raise ValueError('cold QoR changed')
 if raw['status']!='RAW_NATIVE_FULL_STA_SUCCESS':return dict(count=cold['count'],admitted=False,reasons=['NO_COMPLETE_RAW_NATIVE_CANDIDATE'],candidate_cpd_ns=None,candidate_wirelength=None,cold_cpd_ns=cpd,cold_wirelength=wire)
 bind(raw)
 if raw['native_exit_code']!=0 or not raw['serialized_file_unchanged']:raise ValueError('invalid raw import')
 for name in ['design.blif','design.net','design.place']:
  if sha(file_named(cold,name))!=sha(file_named(raw,name)):raise ValueError('different target '+name)
 ccmd,rcmd=cold['command'],raw['command']
 if sha(ccmd[0])!=sha(rcmd[0]) or sha(ccmd[1])!=sha(rcmd[1]):raise ValueError('different native tool/architecture')
 for option in ['--read_rr_graph','--route_chan_width','--num_workers']:
  a,b=ccmd[ccmd.index(option)+1],rcmd[rcmd.index(option)+1]
  if (sha(a)!=sha(b)) if option=='--read_rr_graph' else (a!=b):raise ValueError('different '+option)
 candidate_cpd,candidate_wire=qos(file_named(raw,'import.log'))
 if Fraction(candidate_cpd)!=Fraction(raw['cpd_ns']):raise ValueError('raw QoR changed')
 return dict(count=cold['count'],**joint_qor(candidate_cpd,candidate_wire,cpd,wire),candidate_cpd_ns=candidate_cpd,candidate_wirelength=candidate_wire,cold_cpd_ns=cpd,cold_wirelength=wire)
