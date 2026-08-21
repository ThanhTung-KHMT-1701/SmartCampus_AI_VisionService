from pathlib import Path
import sys
base = Path('evidence/buoi-01')
required = ['README.md','checklist.md','known-issues.md','tool-versions.txt','docker-version.txt','compose-version.txt','hello-world.txt','image-list.txt','smoke-test-result.txt','git-log.txt','service-boundary.md']
missing = [x for x in required if not (base/x).exists()]
errors = []
if missing: errors.append('Missing: ' + ', '.join(missing))
log = (base/'smoke-test-result.txt').read_text(encoding='utf-8', errors='ignore') if (base/'smoke-test-result.txt').exists() else ''
if '[FAIL]' in log: errors.append('Smoke test contains [FAIL]. Fix or document and ask lecturer for approval.')
boundary = (base/'service-boundary.md').read_text(encoding='utf-8', errors='ignore') if (base/'service-boundary.md').exists() else ''
for kw in ['Actor','Boundary','Service','Input','Output','API']:
    if kw.lower() not in boundary.lower(): errors.append(f'service-boundary.md missing keyword/section: {kw}')
if errors:
    print('FAIL')
    for e in errors: print('-', e)
    sys.exit(1)
print('PASS: Session 01 package is structurally complete.')
