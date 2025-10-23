
from typing import Optional
from enum import Enum, auto
import logging

from tools.pid.params import DependentTuningParams, TuningType


logger = logging.getLogger(__name__)


class TuningModifier(Enum):
    """
    Enum representing modifiers for PID tuning, typically for PID controllers only.
    """
    PESSEN_INTEGRAL_RULE = auto()
    SOME_OVERSHOOT = auto()
    NO_OVERSHOOT = auto()


def ziegler_nichols(
    ku: float, 
    tu: float,
    tuning_type: TuningType = TuningType.PI,
    tuning_modifier: Optional[TuningModifier] = None
) -> DependentTuningParams:
    """
    Ziegler-Nichols PID tuning method implementation.

    References:
        - https://en.wikipedia.org/wiki/Ziegler%E2%80%93Nichols_method


    Args:
        ku (float): The ultimate gain (Ku) of the system.
        tu (float): The ultimate period (Tu) of the system.
        tuning_type (TuningType): The type of controller to tune (P, PI, PD, PID).
        tuning_modifier (Optional[TuningModifier]): The tuning modifier to apply.

    Returns:
        DependentTuningParams: The calculated PID parameters.
    """
    if (tuning_type != TuningType.PID) and (tuning_modifier is not None):
        logger.warning(f"Tuning modifier ({tuning_modifier}) is only applicable for PID controllers. Will be ignored for {tuning_type} controller.")
        
    if tuning_type == TuningType.P:
        return DependentTuningParams(
            kp=ku * 0.5,
            ti=0.0,
            td=0.0,
        )
    elif tuning_type == TuningType.PI:
        return DependentTuningParams(
            kp=ku * 0.45,
            ti=tu / 1.2,
            td=0.0,
        )
    elif tuning_type == TuningType.PD:
        return DependentTuningParams(
            kp=ku * 0.8,
            ti=0.0,
            td=tu / 8.0,
        )
    elif tuning_type == TuningType.PID:
        if not tuning_modifier:
            return DependentTuningParams(
                kp=ku * 0.6,
                ti=tu / 2.0,
                td=tu / 8.0,
            )
        elif tuning_modifier == TuningModifier.PESSEN_INTEGRAL_RULE:
            return DependentTuningParams(
                kp=ku * 0.7,
                ti=tu * 0.4,
                td=tu * 0.15,
            )
        elif tuning_modifier == TuningModifier.SOME_OVERSHOOT:
            return DependentTuningParams(
                kp=ku / 3,
                ti=tu / 2,
                td=tu / 3,
            )
        elif tuning_modifier == TuningModifier.NO_OVERSHOOT:
            return DependentTuningParams(
                kp=ku / 5,
                ti=tu / 2,
                td=tu / 3,
            )
        else:
            raise ValueError(f"Unsupported tuning modifier: {tuning_modifier}")
    else:
        raise ValueError(f"Unsupported tuning type: {tuning_type}")