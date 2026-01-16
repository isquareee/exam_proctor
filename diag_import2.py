import importlib, traceback, sys
try:
    importlib.reload(importlib.import_module('auth'))
    m = importlib.import_module('auth')
    print('Imported auth module:', m)
    print('module file:', getattr(m, '__file__', None))
    print('AuthManager in module?:', hasattr(m, 'AuthManager'))
    print('module dict keys sample:', list(m.__dict__.keys())[:40])
except Exception:
    print('Import raised exception:')
    traceback.print_exc()

# Try importing in a fresh process via subprocess to capture real traceback
print('\n--- subprocess import test ---')
import subprocess, sys
res = subprocess.run([sys.executable, '-c', "import importlib, traceback;\ntry:\n import importlib; importlib.import_module('auth'); print('OK')\nexcept Exception as e:\n traceback.print_exc()"], capture_output=True, text=True)
print('returncode:', res.returncode)
print('stdout:\n', res.stdout)
print('stderr:\n', res.stderr)
