#!/usr/bin/env python3

# Being lazy, this one just outputs to stdout

from collections import defaultdict
from subprocess import Popen, PIPE

global_ignorepaths = ('/proc/', '/tmp/', '/var/tmp/', '/SYS', '/drm', '/dev/zero', '/dev/shm/', '/var/log/', '/var/lib/dpkg/', '/var/storage/', '/run/bacula','/run/shm','/run/lock','/[aio]',)

if __name__ == "__main__":
    matches = defaultdict(set)
    currentprocess = None

    pipe = Popen('lsof -F0 -n', shell=True, stdout=PIPE)

    for l in pipe.stdout:
        l = l.decode('utf-8')
        fields = dict([(t[0], t[1:]) for t in l.split('\0') if t != ''])
        if l.startswith('p'):
            currentprocess = fields
            continue

        if not l.startswith('f'):
            raise Exception("Unknown line in lsof output: %s" % l)

        path = fields['n']
        if any(path.startswith(p) for p in global_ignorepaths):
            continue

        if ".dpkg-" in path or "(deleted)" in path or "path inode=" in path or fields['f'] == "DEL":
            matches[currentprocess['c']].add(currentprocess['p'])

    pipe.stdout.close()

    if matches:
        print("\n".join("%s: %s" % (k, ','.join(map(str, v))) for k,v in matches.items()))
