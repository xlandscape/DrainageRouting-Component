from typing import NamedTuple, Type, TypeVar, Dict, Optional, Any, get_type_hints, List
from pathlib import Path
import tomllib
import re

ConfigType = TypeVar("ConfigType", bound=NamedTuple)


def load_config(
    config_file_path: Path, root_config_type: Type[ConfigType], squeeze: bool = False
    ) -> ConfigType:
    """Load a TOML configuration and returns it a nested namedtuple.

    Args:
        config_file_path: path to TOML config file
        root_config_type: type of config
        squeeze: if true (default) and the root config contains only
            one section the returned this section will be returned,
            rather than the root.

    Returns:
        The loaded TOML config
    """
    with open(config_file_path, "rb") as f:
        config_dict = dict(tomllib.load(f))
    config = process_config(interpolate_config(config_dict), root_config_type)
    if squeeze and len(config) == 1:
        return config[0]
    else:
        return config


def interpolate_config(
    config_dict: Dict[str, Any], root_dict: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Interpolates config variables.

    String variables may have macro's of the form ``${section.subsection.variable}``.
    These will be expanded to the corresponding variable in the config. If no
    (sub)section is specified, i.e. ``${variable}`` then the variable is assumed to
    be present in the same (sub)section.

    Args:
        config_dict: the dict to interpolate
        root_dict: root dictionary, needed in case of references to variables outside config_dict.
    """

    def nested_get(dic, keys):
        for key in keys:
            dic = dic[key]
        return dic

    def replace(
        match, config_dict: Dict[str, Any], root_dict: Optional[Dict[str, Any]] = None
    ):
        keys = match.group(1).split(".")  # only variable name, ${var}
        if len(keys) == 1:
            val = match.string.replace(match.group(0), nested_get(config_dict, keys))
        else:  # (sub)section(s) plus variable, ${sect.subsect.var}
            val = match.string.replace(match.group(0), nested_get(root_dict, keys))
        return val

    if not root_dict:
        root_dict = config_dict.copy()
    for key, val in config_dict.items():
        if type(val) is dict:
            config_dict[key] = interpolate_config(val, root_dict)
        else:
            while type(val) is str and (match := re.match("\$\{(.+)\}", val)):
                val = replace(match, config_dict, root_dict)

            config_dict[key] = val
    return config_dict


def process_config(
    config_dict: Dict[str, Any], root_config_type: Type[ConfigType]
) -> ConfigType:
    """Processes a dict with a TOML config and converts it to a nested namedtuple.

    Variables are processed by toml.load(). Additionally variables of type `Path` and
    `List[str]` are converted to such.

    Args:
        config_dict: dict to process
        root_config_type: the config type which should be returned
    """

    def is_config_section(var):
        """Identifies a config section."""
        return (
            type(var) is type
            and issubclass(var, tuple)
            and hasattr(var, "__annotations__")
        )

    config_type_spec = get_type_hints(root_config_type)
    for key, val in config_dict.items():
        value_type = config_type_spec[key]
        if is_config_section(value_type):
            config_dict[key] = process_config(val, value_type)
        elif value_type in [Path]:
            config_dict[key] = value_type(val)
        elif value_type == List[str]:
            config_dict[key] = val.split(",")

    return root_config_type(**config_dict)  # type: ignore
