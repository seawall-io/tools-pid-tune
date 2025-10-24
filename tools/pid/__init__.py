from .params import (
    TuningParams, 
    DependentTuningParams,
    IndependentTuningParams,
    ParallelTuningParams,
)


ALL_TUNING_PARAM_FORMATS: set[type[TuningParams]] = {
    DependentTuningParams,
    IndependentTuningParams,
    ParallelTuningParams,
}
