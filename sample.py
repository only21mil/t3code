import json, pathlib, re, sys, time, datetime
ROOT = pathlib.Path('/home/victor/work/fd-capacity-20261026')
def keyed(path):
    return {p[0].rstrip(':'): int(p[1]) for l in pathlib.Path(path).read_text().splitlines() if len(p := l.split()) >= 2 and p[1].isdigit()}
def snap():
    pressure = {}
    for kind in ['io', 'memory']:
        for l in pathlib.Path('/proc/pressure/' + kind).read_text().splitlines():
            p = l.split(); pressure[kind + '_' + p[0]] = int(dict(x.split('=') for x in p[1:])['total'])
    disks = {}
    for l in pathlib.Path('/proc/diskstats').read_text().splitlines():
        p = l.split()
        if re.fullmatch(r'nvme\d+n\d+', p[2]): disks[p[2]] = {'read_sectors': int(p[5]), 'write_sectors': int(p[9])}
    procs = {}
    for p in pathlib.Path('/proc').iterdir():
        if not p.name.isdigit(): continue
        try:
            io = keyed(p/'io'); comm = (p/'comm').read_text().strip(); holders = []
            for fd in (p/'fd').iterdir():
                try:
                    target = str(fd.readlink())
                    if re.search(r'\.(?:db|sqlite|sqlite3)(?:-wal|-shm)?(?: \(deleted\))?$', target): holders.append(target)
                except OSError: pass
            procs[p.name] = {'comm':comm,'read_bytes':io.get('read_bytes',0),'write_bytes':io.get('write_bytes',0),'db_fd_metadata':sorted(set(holders))}
        except (OSError, ValueError): pass
    return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mono':time.monotonic(),'load':pathlib.Path('/proc/loadavg').read_text().split()[:3], 'pressure':pressure,'mem':keyed('/proc/meminfo'),'vm':keyed('/proc/vmstat'),'disks':disks,'processes':procs}
label=sys.argv[1]; start=snap(); samples=[start]
deadline=start['mono']+10
for i in range(1,11):
    time.sleep(max(0,start['mono']+i-time.monotonic()))
    samples.append(snap())
end=samples[-1]; dt=end['mono']-start['mono']; result={'label':label,'duration_s':dt,'samples':samples}
result['summary']={'start_utc':start['utc'],'end_utc':end['utc'],'load_start':start['load'],'load_end':end['load'],'available_gib_min':min(s['mem']['MemAvailable'] for s in samples)/1048576,'swap_used_gib_start':(start['mem']['SwapTotal']-start['mem']['SwapFree'])/1048576,'swap_used_gib_end':(end['mem']['SwapTotal']-end['mem']['SwapFree'])/1048576,'swap_in_pages':end['vm']['pswpin']-start['vm']['pswpin'],'swap_out_pages':end['vm']['pswpout']-start['vm']['pswpout'],'psi_interval_pct':{k:(end['pressure'][k]-v)/dt/10000 for k,v in start['pressure'].items()},'nvme_mib_s':{k:sum((end['disks'][d][k+'_sectors']-v[k+'_sectors'])*512 for d,v in start['disks'].items())/dt/1048576 for k in ['read','write']}}
(ROOT/'metrics'/f'{label}.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result['summary']))
