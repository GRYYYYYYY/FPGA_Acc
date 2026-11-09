"""Verify whole-net retry/rescue scheduling from reconstructed authority snapshots."""
from collections import defaultdict


def verify_schedule(command, selection, iterations, passes, snapshots, initial):
    enabled = int(command[18]) if len(command) >= 19 else 0
    assert enabled in (0, 1)
    tasks = defaultdict(list)
    for task, row in selection.items(): tasks[row['net']].append(task)
    for group in tasks.values(): group.sort()
    pass_keys = [(r['repeat'], r['iteration'], r['net'], r['pass']) for r in passes]
    assert len(pass_keys) == len(set(pass_keys))
    used_passes = used_searches = rescues = deferred_calls = 0
    search_cursor = defaultdict(int)
    for iteration in iterations:
        rep, epoch = iteration['repeat'], iteration['iteration']
        records = [r for r in passes if r['repeat'] == rep and r['iteration'] == epoch]
        groups = defaultdict(list)
        for row in records: groups[row['net']].append(row)
        expected_nets = sorted((n for r, e, n in initial if (r, e) == (rep, epoch)), key=lambda n: tasks[n][0])
        assert list(groups) == expected_nets
        expected_order = [(net, i) for net in expected_nets for i in range(len(groups[net]))]
        assert [(r['net'], r['pass']) for r in records] == expected_order
        retries = 0
        for net in expected_nets:
            count, reached = initial[rep, epoch, net]
            status = {}; rescue = False
            for pass_number, row in enumerate(groups[net]):
                used_passes += 1; before = count; failed = deferred = 0
                mode = (2 if rescue else 1) if enabled else 0
                for task in tasks[net]:
                    if pass_number and status[task] == 0: continue
                    if pass_number: retries += 1
                    sink = selection[task]['sink']
                    if sink in reached: status[task] = 0; continue
                    key = rep, search_cursor[rep]; search_cursor[rep] += 1; used_searches += 1
                    snap = snapshots[key]; call = snap['call']
                    assert (call['iteration'], call['task'], call['pass'], call['fallback_mode']) == (epoch, task, pass_number, mode)
                    assert snap['before'] == (count, reached)
                    count, reached = snap['after']; assert count >= before
                    status[task] = call['status']; assert status[task] >= 0
                    if status[task] != 0:
                        failed += 1; deferred += call['budget_deferrals']
                enter_rescue = bool(enabled and not rescue and deferred and count == before)
                retry = bool(failed and count > before) or enter_rescue
                assert (row['rescue'], row['tree_before'], row['tree_after'], row['failed_tasks'], row['budget_deferred'], row['will_retry']) == (int(rescue), before, count, failed, deferred, int(retry))
                assert retry == (pass_number+1 < len(groups[net]))
                if enter_rescue: rescue = True; rescues += 1
                deferred_calls += deferred
        assert iteration['deferred_retries'] == retries
    assert used_passes == len(passes) and used_searches == len(snapshots)
    return dict(controller_schedule_verified=True, passes=used_passes, rescue_transitions=rescues,
                accepted_budget_deferrals=deferred_calls, searches=used_searches)
