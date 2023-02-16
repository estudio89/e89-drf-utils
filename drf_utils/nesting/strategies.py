from rest_framework import serializers, fields
from typing import Any, Dict, cast, Protocol, Optional
from django.db import models


class NestedPreSaveStrategy(Protocol):
    def __call__(
        self,
        serializer: "serializers.ModelSerializer",
        field_name: "str",
        parent_instance: "Optional[models.Model]",
        data: "Optional[Dict[str, Any]]",
    ) -> "Optional[models.Model]":
        ...

class NestedPostSaveStrategy(Protocol):
    def __call__(
        self,
        serializer: "serializers.ModelSerializer",
        field_name: "str",
        parent_instance: "models.Model",
        data: "Dict[str, Any]",
    ) -> "None":
        ...


def update_reverse_foreign_key_strategy(
    serializer: "serializers.ModelSerializer",
    field_name: "str",
    parent_instance: "models.Model",
    data: "Dict[str, Any]",
):
    """Updates the parent object using the REVERSE_FOREIGN_KEY strategy."""
    model_field: "models.ManyToOneRel" = serializer.Meta.model._meta.get_field(
        field_name
    )
    reverse_relation = model_field.get_accessor_name()
    fk_parent_field_name = model_field.field.name

    serializer_field = cast("Dict[str, fields.Field]", serializer.fields)[field_name]
    serializer_field.initial_data = data
    serializer_field.instance = getattr(parent_instance, reverse_relation)

    if hasattr(serializer_field, "_validated_data"):
        delattr(serializer_field, "_validated_data")

    serializer_field.is_valid(raise_exception=True)

    save_kwargs = {
        fk_parent_field_name: parent_instance,
        "fk_parent_field_name": fk_parent_field_name,
    }

    serializer_field.save(**save_kwargs)

def update_foreign_key_strategy(
    serializer: "serializers.ModelSerializer",
    field_name: "str",
    parent_instance: "Optional[models.Model]",
    data: "Optional[Dict[str, Any]]",
):
    """Updates the parent object using the FOREIGN_KEY strategy."""
    serializer_field = cast("Dict[str, fields.Field]", serializer.fields)[field_name]
    serializer_field.initial_data = data
    if parent_instance:
        serializer_field.instance = getattr(parent_instance, field_name)
    else:
        serializer_field.instance = None

    if hasattr(serializer_field, "_validated_data"):
        delattr(serializer_field, "_validated_data")

    serializer_field.is_valid(raise_exception=True)
    if not data:
        return None

    return serializer_field.save()

def update_reverse_one_to_one_strategy(
    serializer: "serializers.ModelSerializer",
    field_name: "str",
    parent_instance: "models.Model",
    data: "Dict[str, Any]",
):
    """Updates the parent object using the REVERSE_ONE_TO_ONE strategy."""
    model_field: "models.ManyToOneRel" = serializer.Meta.model._meta.get_field(
        field_name
    )
    reverse_relation = model_field.get_accessor_name()
    fk_parent_field_name = model_field.field.name
    remote_model = model_field.related_model

    serializer_field = cast("Dict[str, fields.Field]", serializer.fields)[field_name]
    serializer_field.initial_data = data
    try:
        serializer_field.instance = getattr(parent_instance, reverse_relation)
    except remote_model.DoesNotExist:
        serializer_field.instance = None
    if hasattr(serializer_field, "_validated_data"):
        delattr(serializer_field, "_validated_data")

    serializer_field.is_valid(raise_exception=True)

    save_kwargs = {
        fk_parent_field_name: parent_instance,
    }

    serializer_field.save(**save_kwargs)


def update_one_to_one_strategy(
    serializer: "serializers.ModelSerializer",
    field_name: "str",
    parent_instance: "Optional[models.Model]",
    data: "Optional[Dict[str, Any]]",
) -> "Optional[models.Model]":
    """Updates the parent object using the ONE_TO_ONE strategy."""

    serializer_field = cast("Dict[str, fields.Field]", serializer.fields)[field_name]
    serializer_field.initial_data = data
    if parent_instance:
        serializer_field.instance = getattr(parent_instance, field_name)
    else:
        serializer_field.instance = None

    if hasattr(serializer_field, "_validated_data"):
        delattr(serializer_field, "_validated_data")

    serializer_field.is_valid(raise_exception=True)

    if serializer_field.instance and not data:
        serializer_field.instance.delete()
        return None

    return serializer_field.save()
