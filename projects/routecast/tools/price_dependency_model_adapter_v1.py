"""Complete model adapter; private fixed standalone kernels, no archived results."""
from pathlib import Path
from price_dependency_search_cache_v2 import Search as Base
class Search(Base):
 def __init__(self,fields,rc,binary):
  expected=Path(__file__).resolve().parents[1]/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so'
  if Path(binary).resolve()!=expected:raise ValueError('unexpected model backend')
  super().__init__(fields,rc,entries=4096,read_limit=65536,output_limit=16384,dependency_total_limit=1048576,output_total_limit=262144)
