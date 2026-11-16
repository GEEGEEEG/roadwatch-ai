import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
with open(root / 'app.py', encoding='utf-8') as f:
    exec(f.read(), {'__file__': str(root / 'app.py'), '__name__': '__main__'})
