import sys
sys.path.insert(0, 'backend')
from scripts.build_dataset_v2 import DEPOSIT_CATALOG

print(f"Total cataloged deposits: {len(DEPOSIT_CATALOG)}")
for i, d in enumerate(DEPOSIT_CATALOG):
    print(f"{i+1:2d}. {d['mine']:<20} | {d['state']:<15} | lat={d['center_lat']:7.4f}, lon={d['center_lon']:7.4f}")
