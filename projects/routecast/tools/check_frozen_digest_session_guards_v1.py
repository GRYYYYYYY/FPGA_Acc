"""Real filesystem invalidation guards for the scoped performance adapter."""
import json
import os
import tempfile
from pathlib import Path
from pre_route_endpoints import sha
from frozen_digest_session_v1 import FrozenDigestSession


def main():
    results=[]
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)
        for mode in ['overwrite_restore_mtime','append','atomic_replace','symlink_retarget','delete']:
            path=root/mode
            target=root/(mode+'_target')
            if mode=='symlink_retarget':
                target.write_bytes(b'abcd');path.symlink_to(target)
            else:path.write_bytes(b'abcd')
            expected=sha(path);session=FrozenDigestSession({str(path):expected},sha)
            assert session(path)==session(path)==expected and session.stats['hits']==1
            old=path.stat()
            if mode=='overwrite_restore_mtime':
                path.write_bytes(b'wxyz');os.utime(path,ns=(old.st_atime_ns,old.st_mtime_ns))
            elif mode=='append':
                with path.open('ab') as f:f.write(b'x')
            elif mode=='atomic_replace':
                replacement=root/'replacement';replacement.write_bytes(b'wxyz');os.replace(replacement,path)
            elif mode=='symlink_retarget':
                replacement=root/'newtarget';replacement.write_bytes(b'wxyz');path.unlink();path.symlink_to(replacement)
            else:path.unlink()
            try:session(path)
            except (ValueError,FileNotFoundError):pass
            else:raise AssertionError(mode)
            results.append(mode)
        mutable=root/'mutable';mutable.write_bytes(b'abcd');session=FrozenDigestSession({},sha)
        first=session(mutable);mutable.write_bytes(b'wxyz');assert session(mutable)!=first and session.stats['hits']==0
        results.append('mutable_path_never_cached')
        path=root/'wrong_manifest';path.write_bytes(b'abcd')
        try:FrozenDigestSession({str(path):'0'*64},sha)(path)
        except ValueError:results.append('wrong_manifest_rejected')
        else:raise AssertionError('wrong manifest')
    print(json.dumps(dict(status='ALL7_REAL_FILESYSTEM_DIGEST_GUARDS_PASS',guards=results)))


if __name__=='__main__':main()
