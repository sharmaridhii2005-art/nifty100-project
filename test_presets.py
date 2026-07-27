from src.screener.engine import ScreenerEngine
from src.screener.presets import *

engine = ScreenerEngine()

print("=" * 60)
print("QUALITY COMPOUNDER")
print("=" * 60)
print(engine.run(QUALITY_COMPOUNDER).head())

print("\n")

print("=" * 60)
print("VALUE PICK")
print("=" * 60)
print(engine.run(VALUE_PICK).head())

print("\n")

print("=" * 60)
print("GROWTH ACCELERATOR")
print("=" * 60)
print(engine.run(GROWTH_ACCELERATOR).head())

print("\n")

print("=" * 60)
print("DIVIDEND CHAMPION")
print("=" * 60)
print(engine.run(DIVIDEND_CHAMPION).head())

print("\n")

print("=" * 60)
print("DEBT FREE BLUE CHIP")
print("=" * 60)


print("\n")

print("=" * 60)
print("TURNAROUND WATCH")
print("=" * 60)
print(engine.run(TURNAROUND_WATCH).head())