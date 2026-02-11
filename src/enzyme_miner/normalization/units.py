from dataclasses import dataclass


@dataclass
class NormalizedValue:
    value: float | None
    unit_normalized: str | None
    warnings: list[str]


def normalize_value(parameter_type: str, value: float | None, unit_raw: str | None) -> NormalizedValue:
    if value is None or not unit_raw:
        return NormalizedValue(value=None, unit_normalized=None, warnings=["unit_not_normalized"])

    unit = unit_raw.strip().lower()

    if parameter_type == "kcat":
        if unit in {"s^-1", "1/s", "s-1"}:
            return NormalizedValue(value=value, unit_normalized="s^-1", warnings=[])
        if unit in {"min^-1", "min-1"}:
            return NormalizedValue(value=value / 60.0, unit_normalized="s^-1", warnings=[])
        if unit in {"h^-1", "h-1", "hr^-1"}:
            return NormalizedValue(value=value / 3600.0, unit_normalized="s^-1", warnings=[])

    if parameter_type == "Km":
        if unit in {"m", "mol/l"}:
            return NormalizedValue(value=value, unit_normalized="M", warnings=[])
        if unit == "mm":
            return NormalizedValue(value=value * 1e-3, unit_normalized="M", warnings=[])
        if unit in {"um", "µm"}:
            return NormalizedValue(value=value * 1e-6, unit_normalized="M", warnings=[])
        if unit == "nm":
            return NormalizedValue(value=value * 1e-9, unit_normalized="M", warnings=[])

    if parameter_type == "kcat_over_Km":
        if unit in {"m^-1 s^-1", "m-1 s-1", "m-1s-1"}:
            return NormalizedValue(value=value, unit_normalized="M^-1 s^-1", warnings=[])
        if unit in {"mm^-1 s^-1", "mm-1 s-1"}:
            return NormalizedValue(value=value * 1e3, unit_normalized="M^-1 s^-1", warnings=[])
        if unit in {"um^-1 s^-1", "µm^-1 s^-1"}:
            return NormalizedValue(value=value * 1e6, unit_normalized="M^-1 s^-1", warnings=[])

    if parameter_type in {"specific_activity", "rate"}:
        if unit in {"umol min^-1 mg^-1", "µmol min^-1 mg^-1"}:
            return NormalizedValue(value=value, unit_normalized="µmol min^-1 mg^-1", warnings=[])
        if unit == "nmol min^-1 mg^-1":
            return NormalizedValue(value=value / 1000.0, unit_normalized="µmol min^-1 mg^-1", warnings=[])
        if unit == "mmol min^-1 mg^-1":
            return NormalizedValue(value=value * 1000.0, unit_normalized="µmol min^-1 mg^-1", warnings=[])
        if unit in {"u/mg", "u mg^-1"}:
            return NormalizedValue(
                value=value,
                unit_normalized="µmol min^-1 mg^-1",
                warnings=["U_definition_assumed"],
            )

    return NormalizedValue(value=None, unit_normalized=None, warnings=["unit_not_normalized"])
