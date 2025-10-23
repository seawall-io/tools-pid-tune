from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum, auto


class TuningType(Enum):
    """
    Enum representing the type of PID controller.
    """
    P = auto()
    PI = auto()
    PD = auto()
    PID = auto()


@dataclass
class TuningParams(ABC):
    """
    Abstract base class for PID tuning parameters.
    """
    def asdict(self):
        """
        Convert the dataclass to a dictionary.
        """
        return asdict(self)

    @property
    @abstractmethod
    def controller_type(self) -> TuningType:
        """
        Return the type of controller (P, PI, PD, PID).
        """
        pass


@dataclass
class DependentTuningParams(TuningParams):
    """
    PID parameters in dependent (time-based) form.
    kp: Proportional gain (unitless)
    ti: Integral time (seconds)
    td: Derivative time (seconds)
    """
    kp: float = field(default=1.0, metadata={"description": "Proportional gain", "units": "unitless"})
    ti: float = field(default=0.0, metadata={"description": "Integral time", "units": "seconds/repeat"})
    td: float = field(default=0.0, metadata={"description": "Derivative time", "units": "seconds"})

    @property
    def controller_type(self) -> TuningType:
        """
        Return the type of controller based on which times are nonzero.
        """
        if self.ti == 0.0 and self.td == 0.0:
            return TuningType.P
        elif self.td == 0.0:
            return TuningType.PI
        elif self.ti == 0.0:
            return TuningType.PD
        else:
            return TuningType.PID

    def to_independent(self) -> IndependentTuningParams:
        """
        Convert dependent (time-based) parameters to independent (gain-based) parameters.
        Returns:
            IndependentTuningParams: The equivalent independent parameters.
        """
        ki = self.kp / self.ti if self.ti != 0 else 0.0
        kd = self.td * self.kp
        return IndependentTuningParams(kp=self.kp, ki=ki, kd=kd)


@dataclass
class IndependentTuningParams(TuningParams):
    """
    PID parameters in independent (gain-based) form.
    kp: Proportional gain (unitless)
    ki: Integral gain (1/seconds)
    kd: Derivative gain (seconds)
    """
    kp: float = field(default=1.0, metadata={"description": "Proportional gain", "units": "unitless"})
    ki: float = field(default=0.0, metadata={"description": "Integral gain", "units": "1/seconds"})
    kd: float = field(default=0.0, metadata={"description": "Derivative gain", "units": "seconds"})

    @property
    def controller_type(self) -> TuningType:
        """
        Return the type of controller based on which gains are nonzero.
        """
        if self.ki == 0.0 and self.kd == 0.0:
            return TuningType.P
        elif self.kd == 0.0:
            return TuningType.PI
        elif self.ki == 0.0:
            return TuningType.PD
        else:
            return TuningType.PID

    def to_dependent(self) -> DependentTuningParams:
        """
        Convert independent (gain-based) parameters to dependent (time-based) parameters.
        Returns:
            DependentTuningParams: The equivalent dependent parameters.
        """
        ti = self.kp / self.ki if self.ki != 0 else 0.0
        td = self.kd / self.kp if self.kp != 0 else 0.0
        return DependentTuningParams(kp=self.kp, ti=ti, td=td)