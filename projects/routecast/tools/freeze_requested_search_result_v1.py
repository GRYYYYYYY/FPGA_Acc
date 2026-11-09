"""Detach only requested-path observations before serial workspace reuse."""
def freeze_requested(source, targets, raw, parents, settled):
    targets=frozenset(targets);settled=frozenset(settled)
    if not settled<=targets:raise ValueError('nonrequested settled target')
    delays={source:raw[source]} if settled else {}
    delays.update({sink:raw[sink] for sink in settled})
    copied={}
    for sink in sorted(settled):
        node=sink;seen=set()
        while node!=source:
            if node in seen:raise ValueError('cyclic borrowed parent chain')
            if node in copied:break
            seen.add(node);previous,slot=parents[node]
            copied[node]=(previous,slot);node=previous
    return delays,copied,settled
