"""Create independent in-memory placement episodes from frozen source records."""
from copy import deepcopy
from prospective_layout_swap_selection_v1 import select_swaps

def make_episodes(blocks, count=3):
    source = deepcopy(list(blocks))
    selection = select_swaps(source, count)
    by_name = {r['name']: r for r in source}
    episodes = []
    for ordinal, swap in enumerate(selection['swaps'], 1):
        left, right = swap['blocks']
        target = deepcopy(source)
        target_by_name = {r['name']: r for r in target}
        target_by_name[left]['location'] = list(by_name[right]['location'])
        target_by_name[right]['location'] = list(by_name[left]['location'])
        # Apply the same schema/occupancy checks to the complete resulting frame.
        select_swaps(target, 0)
        changed = sorted(n for n in by_name if tuple(by_name[n]['location']) != tuple(target_by_name[n]['location']))
        if changed != sorted([left, right]):
            raise ValueError('unexpected changed block set')
        for name in by_name:
            old = {k: v for k, v in by_name[name].items() if k != 'location'}
            new = {k: v for k, v in target_by_name[name].items() if k != 'location'}
            if old != new:
                raise ValueError('nonlocation metadata changed')
        if {tuple(r['location']) for r in target} != {tuple(r['location']) for r in source}:
            raise ValueError('occupied site set changed')
        episodes.append({'episode': ordinal, 'changed_blocks': changed, 'swap': deepcopy(swap), 'blocks': target})
    return {'selection': selection, 'episodes': episodes}
