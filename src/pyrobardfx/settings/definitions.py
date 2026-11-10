"""Setting definitions: what a settings card needs to show one setting, from the JSON schema."""

from typing import Any

from pydantic import BaseModel, ConfigDict, JsonValue

from pyrobardfx.settings.constants import (
    DEFAULT_KEY,
    DEFS_KEY,
    ENUM_KEY,
    GROUP_KEY,
    HELP_KEY,
    LABEL_KEY,
    MAXIMUM_KEY,
    MINIMUM_KEY,
    PROPERTIES_KEY,
    REF_KEY,
    REF_SEPARATOR,
    TYPE_KEY,
    UNMODELLED_CONSTRAINT_KEYS,
    UNMODELLED_CONSTRAINT_MESSAGE,
    SettingGroup,
)
from pyrobardfx.store.constants import EXTRA_FORBID


class SettingDefinition(BaseModel):
    """One setting as the model's JSON schema defines it."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    name: str
    label_key: str
    help_key: str
    group: SettingGroup
    kind: str
    default: JsonValue
    minimum: int | float | None
    maximum: int | float | None
    choices: tuple[str, ...]


class SettingDefinitions:
    """Turns a settings model's JSON schema into one definition per field, in field order."""

    @staticmethod
    def of(model: type[BaseModel]) -> tuple[SettingDefinition, ...]:
        schema = model.model_json_schema()
        definitions = schema.get(DEFS_KEY, {})
        return tuple(
            SettingDefinitions._one(name, SettingDefinitions._resolved(field, definitions))
            for name, field in schema[PROPERTIES_KEY].items()
        )

    # A JSON schema is untyped JSON: pydantic hands it over with `Any` values.
    @staticmethod
    def _resolved(field: dict[str, Any], definitions: dict[str, Any]) -> dict[str, Any]:
        """Merge the shared definition a field refers to, such as an enum, into the field."""
        if REF_KEY not in field:
            return field
        shared = definitions[field[REF_KEY].rsplit(REF_SEPARATOR, 1)[-1]]
        return {**shared, **field}

    @staticmethod
    def _one(name: str, field: dict[str, Any]) -> SettingDefinition:
        """The definition of one field; a constraint the definition cannot carry is refused."""
        for key in UNMODELLED_CONSTRAINT_KEYS:
            if key in field:
                raise ValueError(UNMODELLED_CONSTRAINT_MESSAGE.format(name=name, key=key))
        return SettingDefinition(
            name=name,
            label_key=field[LABEL_KEY],
            help_key=field[HELP_KEY],
            group=field[GROUP_KEY],
            kind=field[TYPE_KEY],
            default=field[DEFAULT_KEY],
            minimum=field.get(MINIMUM_KEY),
            maximum=field.get(MAXIMUM_KEY),
            choices=tuple(field.get(ENUM_KEY, ())),
        )
