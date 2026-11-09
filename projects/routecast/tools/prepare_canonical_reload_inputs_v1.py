"""Copy complete native reload inputs, including explicit original SDC."""
import re
import shutil
from pathlib import Path
from pre_route_endpoints import sha

def prepare(source,destination,*,sdc_required):
    source,destination=Path(source),Path(destination)
    if type(sdc_required) is not bool:raise ValueError('SDC policy must be explicit')
    required=['design.blif','design.net.post_routing','design.place']+(['design.sdc'] if sdc_required else [])
    if any(not (source/name).is_file() for name in required):raise ValueError('missing required native reload input')
    destination.mkdir(exist_ok=False);bindings={str((source/name).resolve()):sha(source/name) for name in required}
    shutil.copyfile(source/'design.blif',destination/'design.blif')
    shutil.copyfile(source/'design.net.post_routing',destination/'design.net')
    if sdc_required:shutil.copyfile(source/'design.sdc',destination/'design.sdc')
    text,count=re.subn(r'Netlist_ID:\s*\S+','Netlist_ID: SHA256:'+sha(destination/'design.net'),(source/'design.place').read_text(),count=1)
    if count!=1:raise ValueError('missing placement netlist identity')
    (destination/'design.place').write_text(text)
    assert (destination/'design.net').read_bytes()==(source/'design.net.post_routing').read_bytes()
    if sdc_required:assert (destination/'design.sdc').read_bytes()==(source/'design.sdc').read_bytes()
    assert all(sha(p)==h for p,h in bindings.items())
    return bindings
