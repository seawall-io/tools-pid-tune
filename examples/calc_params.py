import argparse
from tools.pid.params import (
    TuningType, 
    TuningParams,
    DependentTuningParams, 
    IndependentTuningParams,
    ParallelTuningParams
)
from tools.pid.tune import ziegler_nichols, TuningModifier


ALL_FORMATS: set[type[TuningParams]] = {
    DependentTuningParams,
    IndependentTuningParams,
    ParallelTuningParams,
}

KU = 6.0  # Ultimate gain (Ku)
TU = 2.5  # Ultimate period (Tu, seconds)

def resolve_format(format_name: str) -> type[TuningParams]:
    for fmt in ALL_FORMATS:
        if fmt.__name__ == format_name:
            return fmt
    raise ValueError(f"Unknown format name: {format_name}")


def print_format_metadata(param_format: type[TuningParams], indent: int = 0) -> None:
    metadata = param_format.fields_metadata()
    print(" " * indent + f"[{param_format.__name__}]:")
    for field_name, meta in metadata.items():
        print(" " * indent + f"- {field_name}:")
        for key, value in meta.items():
            print(" " * (indent + 4) + f"{key}: {value}")

def print_params(
    params: DependentTuningParams, 
    formats: set[type[TuningParams]] = ALL_FORMATS,
    indent: int = 0,
) -> None:
    for param_format in formats:
        p = params.convert(to=param_format)
        print(" " * indent + f"{p}")


def explore_tuning(
    ku: float = KU, 
    tu: float = TU, 
    formats: set[type[TuningParams]] = ALL_FORMATS
) -> None:
    print(f"Ziegler-Nichols Tuning Parameters for Ku={ku}, Tu={tu}:")
    print('-' * 50)
    print("Tuning Parameter Format Information:")
    for param_format in formats:
        print_format_metadata(param_format, indent=2)
    print('-' * 50)
    for ttype in TuningType:
        print(f"- {ttype.name}:")
        params = ziegler_nichols(ku, tu, tuning_type=ttype)
        print_params(params, formats=formats, indent=4)
        if ttype == TuningType.PID:
            for modifier in TuningModifier:
                mod_params = ziegler_nichols(ku, tu, tuning_type=ttype, tuning_modifier=modifier)
                print(f"    [{modifier.name}]:")
                print_params(mod_params, formats=formats, indent=6)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Explore Ziegler-Nichols tuning parameters.")
    parser.add_argument("--ku", type=float, default=KU, help="Ultimate gain (Ku)")
    parser.add_argument("--tu", type=float, default=TU, help="Ultimate period (Tu)")
    parser.add_argument(
       '--format',
        action='append',         # Allow the flag to be used multiple times
        default=ALL_FORMATS,
        type=resolve_format,     # Run this function on each value given
        dest='formats',     # Store the results in 'args.format_types'
        help='Specify one or more tuning parameter formats to use (by class name). Defaults to: '
             f"{', '.join(fmt.__name__ for fmt in ALL_FORMATS)})")
    args = parser.parse_args()

    explore_tuning(ku=args.ku, tu=args.tu, formats=args.formats)