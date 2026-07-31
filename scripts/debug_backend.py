from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('gen','scripts/generate_security_reports.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
req = mod.read_text(Path('requirements.txt'))
print(repr(req[:200]))
print('flask' in req.lower())
print(req.lower().find('flask'))
print(mod.ROOT)
print(mod.detect_backend())
