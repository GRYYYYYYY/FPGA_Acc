"""Mechanical, fail-closed instrumentation of the bound b32 production search.
Only widen result/path counts, record resource loads, and observe MQ occupancy.
A 65535 recording guard is selectable as a counterfactual, not a historical binary.
"""
import pathlib,sys,hashlib
src=pathlib.Path(sys.argv[1]); dst=pathlib.Path(sys.argv[2])
s=src.read_text()
replacements=[('#include "persistroute.hpp"','#include "diagnostic.hpp"'),
 ('search_hbm_kernel','wide_search'),('PathResult','WideResult'),
 ('||path_entries>=65535U',''),('static_cast<std::uint16_t>(path_entries)','static_cast<std::uint32_t>(path_entries)'),
 ('hbm_mq_push(', 'observe_push('),
 ('++out.edge_visits;const Resource state=resources[edge.dst];','++out.edge_visits;const Resource state=resources[edge.dst];if(!observe_read(edge.dst)){overflow=true;break;}')]
for a,b in replacements:
 if a not in s: raise RuntimeError('unmatched transform '+a)
 s=s.replace(a,b)
s=s.replace('if(found&&!overflow){','observation.score_calls=observation.calls;observation.score_unique=observation.ids.size();observation.limit=0xffffffffU;if(found&&!overflow){')
s=s.replace('path_pool[path_cursor++]=cursor;', 'observe_read(cursor);path_pool[path_cursor++]=cursor;')
s=s.replace('if(!found||overflow){','if(!found||overflow){if(observation.failure=="none")observation.failure=overflow?"other_capacity_or_input":"exhausted_under_hop_bound";')
dst.write_text(s)
