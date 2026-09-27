import os
import pandas as pd
from pathlib import Path

pdir = Path('backend/data/production')
for f in sorted(pdir.glob('*')):
    if f.is_file() and not f.name.startswith('.'):
        try:
            df = pd.read_csv(f) if f.suffix == '.csv' else pd.read_excel(f)
            print(f'=== {f.name} ===')
            print(f'Shape: {df.shape}')
            print(f'Columns ({len(df.columns)}): {list(df.columns)}')
            print(f'Sample:\n{df.head(1).to_dict(orient="records")}\n')
        except Exception as e:
            print(f'Error reading {f.name}: {e}')
