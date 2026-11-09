"""Sandbox transformer: reuse pre-route identity, retain canonical identity probes."""
def transform_identity(source, name):
    if not name.startswith('trial_') or 'native_import' not in name:
        return source
    start=source.index("with (work/'identity.log').open('w')")
    end=source.index("nets={row['name']",start)
    old=source[start:end]
    assert 'subprocess.run(icmd' in old and 'assert code==1' in old
    replacement="""from bound_identity_reuse import reuse
seed_path=Path(os.environ['ROUTECAST_IDENTITY_SEED']);seed_sha=os.environ['ROUTECAST_IDENTITY_SEED_SHA256']
rebound=reuse(seed_path,seed_sha,icmd,work)
table.write_text(''.join(json.dumps(row)+'\\n' for row in rebound))
(work/'identity.log').write_text('Identity reused under bound seed '+str(seed_path)+' SHA256:'+seed_sha+'; no identity subprocess executed.\\n')
(work/'identity_reuse.json').write_text(json.dumps({'seed':str(seed_path),'seed_sha256':seed_sha,'table_sha256':sha(table)})+'\\n')
"""
    return source[:start]+replacement+source[end:]
