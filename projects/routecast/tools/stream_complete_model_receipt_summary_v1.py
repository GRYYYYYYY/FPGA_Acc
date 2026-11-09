"""Bounded full receipt statistics, never a physical/event correctness audit."""
import math, json
from collections import Counter
from bounded_model_json_stream_v1 import Reader


class ReceiptReader(Reader):
    def value(self):
        self.peek()
        while True:
            try:
                value,end=self.decoder.raw_decode(self.buffer,self.pos)
                if end-self.pos>self.max_value:raise ValueError('JSON value exceeds bound')
                if end==len(self.buffer) and not self.eof:
                    self.more();continue
                # raw_decode can accept the integer prefix of a split decimal
                # or exponent (e.g. "3." or "3e+"). Require a token delimiter.
                if end<len(self.buffer) and self.buffer[end] not in ' \t\r\n,]}:':
                    raise json.JSONDecodeError('unfinished or invalid token',self.buffer,end)
                self.pos=end
                return value
            except json.JSONDecodeError:
                if self.eof:raise
                if len(self.buffer)-self.pos>=self.max_value:raise ValueError('JSON value exceeds bound')
                self.more()


def summarize(path,chunk=65536):
    result={'timers':{},'rounds':[]};found=False
    with open(path) as stream:
        reader=ReceiptReader(stream,chunk=chunk)
        for key in reader.keys():
            if key!='rounds':
                value=reader.value()
                if key.endswith('_seconds'):
                    if type(value) not in (int,float) or not math.isfinite(value) or value<0:raise ValueError('invalid timer')
                    result['timers'][key]=value
                continue
            found=True;reader.expect('[')
            if reader.peek()==']':reader.pos+=1;continue
            while True:
                metadata={};counts=Counter();net_ids=[];fallback=0;events_found=False
                for member in reader.keys():
                    if member!='events':metadata[member]=reader.value();continue
                    events_found=True
                    for event in reader.array():
                        if type(event) is not dict or type(event.get('net_id')) not in (str,int) or type(event.get('status')) is not str:raise ValueError('invalid event identity/status')
                        net_ids.append(event['net_id']);counts[event['status']]+=1;fallback+=int('fallback' in event)
                index=len(result['rounds'])
                if not events_found or type(metadata.get('round_index')) is not int or metadata['round_index']!=index:raise ValueError('round identity/events missing')
                if len(net_ids)!=len(set(net_ids)) or metadata.get('affected_nets')!=net_ids:raise ValueError('duplicate or mismatched event schedule')
                for field in ('overflow_before','overflow_after'):
                    if type(metadata.get(field)) is not int or metadata[field]<0:raise ValueError('invalid overflow metadata')
                seconds=metadata.get('seconds')
                if type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0:raise ValueError('invalid round seconds')
                result['rounds'].append(dict(round_index=index,seconds=seconds,events=len(net_ids),status_counts=dict(counts),fallback_calls=fallback,overflow_before=metadata['overflow_before'],overflow_after=metadata['overflow_after']))
                if reader.peek()==']':reader.pos+=1;break
                reader.expect(',')
        reader.finish()
    if not found or not result['rounds']:raise ValueError('missing nonempty rounds')
    result['scope']='Complete strict JSON receipt traversal and metadata/statistics only; no independent path, objective, epoch or ledger audit, and no paired performance proof.'
    return result
