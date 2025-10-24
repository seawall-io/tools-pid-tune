from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field, fields, Field, is_dataclass
from typing import Self, Optional, TypeVar, Any, Mapping
from enum import Enum, StrEnum, auto
from typing import cast

class MetadataKeys(StrEnum):
    """
    Enum for metadata keys used in dataclass fields.
    """
    DESCRIPTION = auto()
    UNITS = auto()


class TuningType(Enum):
    """
    Enum representing the type of PID controller.
    """
    P = auto()
    PI = auto()
    PD = auto()
    PID = auto()


def make_metadata(
    description: Optional[str] = None, 
    units: Optional[str] = None
) -> dict | None:
    """
    Helper function to create metadata dictionary for dataclass fields.
    Args:
        description (str): Description of the field.
        units (str): Units of the field.
    Returns:
        dict | None: Metadata dictionary or None if both fields are None.
    """
    metadata = {}
    if description:
        metadata[MetadataKeys.DESCRIPTION.value] = description
    if units:
        metadata[MetadataKeys.UNITS.value] = units

    return metadata or None

def make_field(
    default: Optional[object] = None,
    description: Optional[str] = None,
    units: Optional[str] = None,
    **kwargs,
) -> Any:
    """
    Helper function to create a dataclass field with metadata.
    Args:
        default (object): Default value for the field.
        description (str): Description of the field.
        units (str): Units of the field.
        **kwargs: Additional keyword arguments for the field.
    Returns:
        Field: The created dataclass field with metadata.
    """
    metadata = make_metadata(description=description, units=units)
    if metadata:
        kwargs['metadata'] = metadata
    return field(default=default,**kwargs)


class TuningParams(ABC):
    """
    Abstract base class for PID tuning parameters.
    """
    def asdict(self):
        """
        Convert the dataclass to a dictionary.
        """
        return asdict(self)
    
    @classmethod
    def fields_dict(self) -> dict[str, Field]:
        """
        Get a dictionary of field names to Field objects.
        Returns:
            dict: A dictionary mapping field names to their Field objects.
        """
        if is_dataclass(self):
            return {f.name: f for f in fields(self)}
        return {}

    @classmethod
    def fields_metadata(cls) -> dict[str, Mapping]:
        """
        Get a dictionary of field names to their metadata.
        Returns:
            dict: A dictionary mapping field names to their metadata dictionaries.
        """
        return {k: v.metadata for k, v in cls.fields_dict().items()}
        

    def extended_dict(self) -> dict:
        flds_dict = self.fields_dict()
        obj_dict = self.asdict()
        extended = {}
        for k, v in obj_dict.items():
            if k in flds_dict:
                extended[k] = {"value": v, "metadata": flds_dict[k].metadata}
        return extended

    @property
    @abstractmethod
    def controller_type(self) -> TuningType:
        """
        Return the type of controller (P, PI, PD, PID).
        """
        pass


T = TypeVar('T', bound=TuningParams)

@dataclass
class DependentTuningParams(TuningParams):
    """
    PID parameters in dependent (time-based) form.
    kp: Proportional gain (unitless)
    ti: Integral time (seconds)
    td: Derivative time (seconds)
    """
    kp: float = make_field(default=1.0, description="Proportional gain")
    ti: float = make_field(default=0.0, description="Integral time", units="seconds/repeat")
    td: float = make_field(default=0.0, description="Derivative time", units="seconds")

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
        
    def convert(self, to: type[T]) -> T:
        """
        Convert to another form of tuning parameters.
        Args:
            to (type[AlternateTuningParams]): The target tuning parameters class.
        Returns:
            AlternateTuningParams: The converted tuning parameters.
        """
        if to == self.__class__:
            return cast(T, self)
        elif issubclass(to, TuningParamsCodec):
            return cast(T, to.from_dependent(dep_params=self))
        else:
            raise ValueError(f"[{self.__class__.__name__}] Unsupported target tuning parameters class: {to}")

class TuningParamsCodec(TuningParams):

    @abstractmethod
    def to_dependent(self) -> DependentTuningParams:
        """
        Convert alternate tuning parameters to dependent (time-based) parameters.
        Returns:
            DependentTuningParams: The equivalent dependent parameters.
        """
        pass

    @classmethod
    @abstractmethod
    def from_dependent(cls, dep_params: DependentTuningParams) -> Self:
        """
        Create alternate tuning parameters from dependent (time-based) parameters.
        Args:
            dep_params (DependentTuningParams): The dependent parameters to convert.
        Returns:
            AlternateTuningParams: The equivalent alternate parameters.
        """
        pass

    @property
    def controller_type(self) -> TuningType:
        """
        Return the type of controller based on the dependent parameters.
        """
        return self.to_dependent().controller_type
    
    def convert(self, to: type[T]) -> T:
        """
        Cast to another form of tuning parameters.
        Args:
            to (type[TuningParams]): The target tuning parameters class.
        Returns:
            TuningParams: The converted tuning parameters.
        """
        return self.to_dependent().convert(to=to)

@dataclass
class IndependentTuningParams(TuningParamsCodec):
    """
    PID parameters in independent (gain-based) form.
    kp: Proportional gain (unitless)
    ki: Integral gain (1/seconds)
    kd: Derivative gain (seconds)
    """
    kp: float = make_field(default=1.0, description="Proportional gain")
    ki: float = make_field(default=0.0, description="Integral gain", units="1/seconds")
    kd: float = make_field(default=0.0, description="Derivative gain", units="seconds")


    def to_dependent(self) -> DependentTuningParams:
        """
        Convert independent (gain-based) parameters to dependent (time-based) parameters.
        Returns:
            DependentTuningParams: The equivalent dependent parameters.
        """
        ti = self.kp / self.ki if self.ki != 0 else 0.0
        td = self.kd / self.kp if self.kp != 0 else 0.0
        return DependentTuningParams(kp=self.kp, ti=ti, td=td)
    
    @classmethod
    def from_dependent(cls, dep_params: DependentTuningParams) -> Self:
        """
        Create independent (gain-based) parameters from dependent (time-based) parameters.
        Args:
            dep_params (DependentTuningParams): The dependent parameters to convert.
        Returns:
            IndependentTuningParams: The equivalent independent parameters.
        """
        return cls(
            kp=dep_params.kp, 
            ki=dep_params.kp / dep_params.ti if dep_params.ti != 0 else 0.0, 
            kd=dep_params.td * dep_params.kp,
        )
    

@dataclass(init=False)
class ParallelTuningParams(TuningParamsCodec):
    """
    PID parameters in parallel form (e.g. those used by Foxboro DCS).
    """
    _pv_min: float = make_field(default=0.0, description="Minimum process variable", units="EU")
    _pv_max: float = make_field(default=100.0, description="Maximum process variable", units="EU")
    pband: float = make_field(default=100.0, description="Proportional band", units="%")
    int: float = make_field(default=0.0, description="Integral time", units="minutes")
    deriv: float = make_field(default=0.0, description="Derivative time", units="minutes")

    def __init__(
        self, 
        pv_min=0, 
        pv_max=100,
        pband: float = 100.0,
        int: float = 0.0,
        deriv: float = 0.0,
    ) -> None:
        self._pv_min = pv_min
        self._pv_max = pv_max
        self.pband = pband
        self.int = int
        self.deriv = deriv

    @property
    def pv_min(self) -> float:
        """
        Get the minimum process variable value.
        """
        return self._pv_min

    @pv_min.setter
    def pv_min(self, value: float):
        """
        Set the minimum process variable value and update pband accordingly.
        """
        if value != self.pv_min:
            if value >= self.pv_max:
                raise ValueError("pv_min must be less than pv_max.")
            old_range = self.pv_range
            self._pv_min = value
            self._update_p_band(old_range=old_range)

    @property
    def pv_max(self) -> float:
        """
        Get the maximum process variable value.
        """
        return self._pv_max

    @pv_max.setter
    def pv_max(self, value: float):
        """
        Set the maximum process variable value and update p_band accordingly.
        """
        if value != self.pv_max:
            if value <= self.pv_min:
                raise ValueError("pv_max must be greater than pv_min.")
            old_range = self.pv_range
            self._pv_max = value
            self._update_p_band(old_range=old_range)

    def _update_p_band(self, old_range: tuple[float, float]):
        """
        Update the proportional band based on pv_min and pv_max.
        """
        old_span = old_range[1] - old_range[0]
        new_range = self.pv_range
        new_span = new_range[1] - new_range[0]
        if old_span != new_span:
            self.pband = self.pband * (new_span / old_span)

    @staticmethod
    def _fix_private_keys(obj_dict: dict) -> dict:
        for k in ('pv_min', 'pv_max'):
            priv_key = f'_{k}'
            if priv_key in obj_dict:
                obj_dict[k] = obj_dict.pop(priv_key)
        return obj_dict
    
    @classmethod
    def fields_dict(self) -> dict[str, Field]:
        return self._fix_private_keys(super().fields_dict())

    def asdict(self) -> dict:
        obj_dict = super().asdict()
        return self._fix_private_keys(obj_dict)

    def extended_dict(self) -> dict:
        obj_dict = super().extended_dict()
        return self._fix_private_keys(obj_dict)

    def __repr__(self) -> str:
        fld_strs = [f"{k}={v}" for k, v in self.asdict().items()]
        return f'{self.__class__.__name__}({{{", ".join(fld_strs)}}})'

   
    @property
    def pv_range(self) -> tuple[float, float]:
        """
        Get the range of the process variable.
        Returns:
            tuple[float, float]: The (min, max) range of the process variable.
        """
        return (self.pv_min, self.pv_max)
    

    def to_dependent(self) -> DependentTuningParams:
        """
        Convert parallel tuning parameters to dependent (time-based) parameters.
        Returns:
            DependentTuningParams: The equivalent dependent parameters.
        """
        return DependentTuningParams(
            kp=100.0 / self.pband if self.pband != 0 else 0.0,
            ti=self.int * 60.0,
            td=self.deriv * 60.0,
        )
    
    @classmethod
    def from_dependent(cls, dep_params: DependentTuningParams) -> Self:
        """
        Create parallel tuning parameters from dependent (time-based) parameters.
        Args:
            dep_params (DependentTuningParams): The dependent parameters to convert.
        Returns:
            ParallelTuningParams: The equivalent parallel parameters.
        """
        return cls(
            pband=100.0 / dep_params.kp if dep_params.kp != 0 else 0.0,
            int=dep_params.ti / 60.0,
            deriv=dep_params.td / 60.0,
        )
