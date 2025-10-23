from tools.pid.params import TuningType
from tools.pid.tune import ziegler_nichols, TuningModifier

# Example ultimate gain and period values
ku = 6.0  # Ultimate gain (Ku)
tu = 2.5  # Ultimate period (Tu, seconds)

# Try all controller types
for ttype in TuningType:
    params = ziegler_nichols(ku, tu, tuning_type=ttype)
    print(f"{ttype.name}: {params}; {params.to_independent()}")
    if ttype == TuningType.PID:
        for modifier in TuningModifier:
            mod_params = ziegler_nichols(ku, tu, tuning_type=ttype, tuning_modifier=modifier)
            print(f"  [{modifier.name}] {mod_params}; {mod_params.to_independent()}")
