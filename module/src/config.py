"""
This module defines the complete contents of the TOML config file in the form of a namedtuple,
and exposes the function `load_config()` which reads a config file and returns the contents as
a named tuple.
"""
from typing import NamedTuple
from pathlib import Path
import xdrainagerouting.module.src as xDR_component


class ConfigRoot(NamedTuple):
    """Root config class; specifies the sections"""

    general: "Config_general"
    xroutingdrainage: "Config_xroutingdrainage"


class Config_general(NamedTuple):
    """General section"""

    runDirRoot: Path
    inputDir: Path
    nProcessor: int
    overwrite: bool
    fields: list
    reaches: list


class Config_xroutingdrainage(NamedTuple):
    xdrainagerouting_file: Path
    output_lineic_file: Path
    outputVars: str
    fieldsAreaFile: Path
    fieldsMassFluxFile: Path
    reachesLengthFile: Path


class Config_pearl(NamedTuple):
    """pearl section"""

    inputDirMeteo: Path
    pearlBinary: Path


class Config(NamedTuple):
    """Section SAFE"""

    AssessmentDirBase: Path
    ApplInterval: str
    GemInstallDir: Path
    StartDayApplWindow: int
    EndDayApplWindow: int
    OutputDir: Path


def load_config(file_path: Path) -> Config:
    """Read TOML config file and returns it as NamedTuple."""
    return xDR_component.configlib.load_config(file_path, ConfigRoot, squeeze=True)
