"""Exact complete-round parity with bounded per-event memory."""
import hashlib,json
from itertools import zip_longest
from stream_complete_model_receipt_summary_v1 import ReceiptReader


def round_items(path,chunk=65536):
    found=False
    with open(path) as stream:
        reader=ReceiptReader(stream,chunk=chunk)
        for key in reader.keys():
            if key!='rounds':reader.value();continue
            found=True;reader.expect('[');index=0
            if reader.peek()==']':reader.pos+=1;continue
            while True:
                metadata={};events=False
                for member in reader.keys():
                    if member!='events':metadata[member]=reader.value();continue
                    events=True
                    for event in reader.array():yield ('event',index,event)
                if not events or type(metadata.get('round_index')) is not int or metadata['round_index']!=index:raise ValueError('invalid round identity/events')
                yield ('metadata',index,{k:v for k,v in metadata.items() if k not in ('seconds','state_file')})
                index+=1
                if reader.peek()==']':reader.pos+=1;break
                reader.expect(',')
        reader.finish()
    if not found:raise ValueError('missing rounds')


def compare(reference,candidate,chunk=65536):
    sentinel=object();rows=[];counts={};hashes={}
    for a,b in zip_longest(round_items(reference,chunk),round_items(candidate,chunk),fillvalue=sentinel):
        if a is sentinel or b is sentinel:raise ValueError('different stream lengths')
        # Canonical JSON also distinguishes integer/float and bool/int domains;
        # object key order is deliberately irrelevant, list order is preserved.
        ca=json.dumps(a,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        cb=json.dumps(b,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        if ca!=cb:raise ValueError('round item differs: '+str(a[:2]))
        kind,index,value=a
        digest=hashes.setdefault(index,hashlib.sha256());digest.update(len(ca).to_bytes(8,'big'));digest.update(ca)
        if kind=='event':counts[index]=counts.get(index,0)+1
        else:rows.append(dict(round_index=index,events=counts.get(index,0),complete_events_and_metadata_sha256=digest.hexdigest()))
    if not rows:raise ValueError('empty rounds')
    return rows
