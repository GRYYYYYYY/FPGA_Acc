"""Strict bounded-value JSON traversal for complete immutable model records.

Large arrays are visited item by item. Unselected values are decoded strictly
then discarded; values exceeding the explicit bound are rejected, never skipped.
"""
import json


def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate JSON object key')
        result[key]=value
    return result


def invalid_constant(value):
    raise ValueError('non-finite JSON constant: '+value)


class Reader:
    def __init__(self,stream,chunk=65536,max_value=16*2**20):
        self.stream=stream;self.chunk=chunk;self.max_value=max_value
        self.buffer='';self.pos=0;self.eof=False
        self.decoder=json.JSONDecoder(object_pairs_hook=unique_object,parse_constant=invalid_constant)
    def more(self):
        self.buffer=self.buffer[self.pos:];self.pos=0
        part=self.stream.read(self.chunk)
        if not part:self.eof=True
        self.buffer+=part
    def peek(self):
        while True:
            while self.pos<len(self.buffer) and self.buffer[self.pos].isspace():self.pos+=1
            if self.pos<len(self.buffer):return self.buffer[self.pos]
            if self.eof:return ''
            self.more()
    def expect(self,char):
        if self.peek()!=char:raise ValueError('unexpected JSON delimiter: '+char)
        self.pos+=1
    def value(self):
        self.peek()
        while True:
            try:
                result,end=self.decoder.raw_decode(self.buffer,self.pos)
                # A number/literal at a chunk boundary may continue in the next
                # chunk. Require its closing delimiter or actual EOF as proof.
                if end==len(self.buffer) and not self.eof:
                    self.more();continue
                if end-self.pos>self.max_value:raise ValueError('JSON value exceeds bound')
                self.pos=end
                return result
            except json.JSONDecodeError:
                if self.eof:raise
                if len(self.buffer)-self.pos>=self.max_value:raise ValueError('JSON value exceeds bound')
                self.more()
    def keys(self):
        self.expect('{');seen=set()
        if self.peek()=='}':self.pos+=1;return
        while True:
            key=self.value()
            if type(key) is not str or key in seen:raise ValueError('duplicate or invalid key')
            seen.add(key);self.expect(':');yield key
            if self.peek()=='}':self.pos+=1;return
            self.expect(',')
    def array(self):
        self.expect('[')
        if self.peek()==']':self.pos+=1;return
        while True:
            yield self.value()
            if self.peek()==']':self.pos+=1;return
            self.expect(',')
    def finish(self):
        if self.peek():raise ValueError('JSON trailing data')


def records(path,field='records',*,max_value=16*2**20):
    found=False
    with open(path) as stream:
        r=Reader(stream,max_value=max_value)
        for key in r.keys():
            if key==field:
                found=True
                yield from r.array()
            else:r.value()
        r.finish()
    if not found:raise ValueError('missing selected record array')


def object_members(path,field,*,max_value=16*2**20):
    found=False
    with open(path) as stream:
        r=Reader(stream,max_value=max_value)
        for key in r.keys():
            if key==field:
                found=True
                for member in r.keys():yield member,r.value()
            else:r.value()
        r.finish()
    if not found:raise ValueError('missing selected member object')


def round_events(path,*,max_value=16*2**20):
    found=False
    with open(path) as stream:
        r=Reader(stream,max_value=max_value)
        for key in r.keys():
            if key!='rounds':r.value();continue
            found=True;r.expect('[');index=0
            if r.peek()==']':r.pos+=1;continue
            while True:
                events=False;round_index=None
                for member in r.keys():
                    if member=='events':
                        events=True
                        for event in r.array():yield index,event
                    elif member=='round_index':round_index=r.value()
                    else:r.value()
                if not events or round_index!=index:raise ValueError('round identity/events missing')
                index+=1
                if r.peek()==']':r.pos+=1;break
                r.expect(',')
        r.finish()
    if not found:raise ValueError('missing rounds')
