"""Console worker retains stdin/stdout even when the GUI is windowed."""
import sys
from softhsm_studio.infrastructure.pkcs11 import worker, key_worker

if __name__ == '__main__':
    operation = sys.argv.pop(1) if len(sys.argv) > 1 else ''
    if operation == 'snapshot':
        raise SystemExit(worker.main())
    if operation == 'keys':
        raise SystemExit(key_worker.main())
    raise SystemExit('Expected snapshot or keys operation.')
