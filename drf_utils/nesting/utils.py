# -*- coding: utf-8 -*-
import uuid
from enum import Enum
from typing import Callable, List, Tuple, TypedDict

from django.db import models, transaction
from rest_framework import serializers

from .strategies import (
    NestedPostSaveStrategy,
    NestedPreSaveStrategy,
    update_foreign_key_strategy,
    update_one_to_one_strategy,
    update_reverse_foreign_key_strategy,
    update_reverse_one_to_one_strategy,
)


class NestedRelationshipType(Enum):
    """Enum that represents the type of relationship between the parent and child objects."""

    ONE_TO_ONE = "one_to_one"
    REVERSE_ONE_TO_ONE = "reverse_one_to_one"
    FOREIGN_KEY = "foreign_key"
    REVERSE_FOREIGN_KEY = "reverse_foreign_key"
    MANY_TO_MANY = "many_to_many"


class NestedSerializerSpec(TypedDict):
    """Specification of a nested serializer.

    Attributes:
        serializer_field_name (str): Name of the serializer field that contains the nested serializer.
        fk_parent_field_name (str): Name of the field that contains the foreign key to the parent object. In the case of a OneToOneField, this field will be the same as the database field that references the parent object.
        reverse_relation (str): Name of the reverse relation of the parent object to the child object.
    """

    serializer_field_name: "str"
    model_field_name: "str"


def save_nested_choice_serializers(field_names: "List[str]") -> "Callable":
    """Decorator to be used in serializers that contain nested serializers that use the CHOICE strategy.

    The CHOICE strategy is used when the nested serializer will never be created or updated, only the relationship with the parent object will be created / updated.

    This decorator must be used in conjunction with the NestedRelationChoiceField class.

    Args:
        field_names (List[str]): List of names of the serializer fields that contain the nested serializers.

    Example:
        If you have two models like this:

            class City(models.Model):
                name = models.CharField(max_length=255)
                state = models.CharField(max_length=255)

            class Address(models.Model):
                city = models.ForeignKey(City, on_delete=models.CASCADE)
                street = models.CharField(max_length=255)
                number = models.CharField(max_length=255)
                neighborhood = models.CharField(max_length=255)

        And you have two serializers like this:

            class CitySerializer(ModelSerializer):
                class Meta:
                    model = City
                    fields = (
                        "id",
                        "name",
                        "state",
                    )

            @save_nested_choice_serializers(field_names=["city"])
            class AddressSerializer(ModelSerializer):
                city = NestedRelationChoiceField(
                    allow_null=True,
                    required=False,
                    serializer_class=CitySerializer,
                )
                class Meta:
                    model = Address
                    fields = (
                        "id",
                        "city",
                        "street",
                        "number",
                        "neighborhood",
                    )

        Then, when the AddressSerializer receives a JSON like this:

            {
                "city": {
                    "id": "1",
                    "name": "New York",
                    "state": "NY"
                },
                "street": "5th Avenue",
                "number": "123",
                "neighborhood": "Manhattan"
            }

        It will create a new Address object with the data from the JSON and associate it with the City object with id 1 but it will not create a new City object or update it.
    """

    def wrapper(klass):
        original = klass.save

        def wrapped(self, *args, **kwargs):
            validated_data = self.validated_data
            nested_validated_data = {}

            for field_name in field_names:
                if validated_data is not None and field_name in validated_data:
                    nested_validated_data[field_name] = validated_data.pop(field_name)

            with transaction.atomic():
                kwargs.update(nested_validated_data)
                parent_instance = original(self, *args, **kwargs)

            return parent_instance

        klass.save = wrapped
        return klass

    return wrapper


def _get_relationship_type(model_class, field_name: "str"):
    """Returns the type of relationship between the parent and child objects.

    Args:
        model_class (Model): Model class of the parent object.
        field_name (str): Name of the field that contains the foreign key to the parent object.

    Returns:
        NestedRelationshipType: Type of relationship between the parent and child objects.
    """
    field = model_class._meta.get_field(field_name)
    if isinstance(field, models.OneToOneField):
        return NestedRelationshipType.ONE_TO_ONE
    elif isinstance(field, models.OneToOneRel):
        return NestedRelationshipType.REVERSE_ONE_TO_ONE
    elif isinstance(field, models.ForeignKey):
        return NestedRelationshipType.FOREIGN_KEY
    elif isinstance(field, models.ManyToOneRel):
        return NestedRelationshipType.REVERSE_FOREIGN_KEY
    elif isinstance(field, models.ManyToManyField):
        return NestedRelationshipType.MANY_TO_MANY
    else:
        raise ValueError(f"Invalid field type: {field}")


def _get_post_save_strategy(
    relationship_type: "NestedRelationshipType",
) -> "NestedPostSaveStrategy":
    strategies_map = {
        NestedRelationshipType.REVERSE_ONE_TO_ONE: update_reverse_one_to_one_strategy,
        NestedRelationshipType.REVERSE_FOREIGN_KEY: update_reverse_foreign_key_strategy,
    }
    strategy = strategies_map.get(relationship_type)
    if strategy is None:
        raise ValueError(f"Invalid relationship type: {relationship_type}")
    return strategy


def _get_pre_save_strategy(
    relationship_type: "NestedRelationshipType",
) -> "NestedPreSaveStrategy":
    strategies_map = {
        NestedRelationshipType.ONE_TO_ONE: update_one_to_one_strategy,
        NestedRelationshipType.FOREIGN_KEY: update_foreign_key_strategy,
    }
    strategy = strategies_map.get(relationship_type)
    if strategy is None:
        raise ValueError(f"Invalid relationship type: {relationship_type}")
    return strategy


def save_nested_serializers(field_names: "List[str]") -> "Callable":
    """Decorator to be used in serializers that contain nested serializers and that use the NESTED strategy.

    The NESTED strategy is used when the objects of the nested serializer will be created if they do not exist or updated if they already exist, always maintaining the relationship with the parent object.

    This decorator must be used in conjunction with the NestedListSerializer class.

    Args:
        field_names (List[str]): List of names of the serializer fields that contain the nested serializers.

    The decorated serializer may optionally contain a method "def post_save_nested_serializers(instance: 'Model', is_created: 'bool') -> 'Model'" that will be called after the creation / update of the nested objects. This method must receive as a parameter the parent object and a boolean indicating whether the object was created or just edited. This method must return the parent object instance received.

    Example:

        Considering the following models:

            class Profile(models.Model):
                birth_date = models.DateField()

            class Address(models.Model):
                city = models.TextField()
                state = models.TextField()
                street = models.TextField()
                number = models.TextField()
                neighborhood = models.TextField()
                profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="addresses")

        The serializers would be defined as shown below. The Perfil serializer would be defined to save the nested addresses in the following way:

            from drf_utils.utils import save_nested_serializers, NestedListSerializer

            class AddressSerializer(ModelSerializer):
                class Meta:
                    model = Address
                    fields = (
                        "id",
                        "city",
                        "state",
                        "street",
                        "number",
                        "neighborhood",
                    )
                    list_serializer_class = NestedListSerializer

            @save_nested_serializers(
                [
                    {
                        "field_name": "addresses",
                        "fk_parent_field_name": "profile",
                        "reverse_relation": "addresses",
                    }
                ]
            )
            class PerfilSerializer(ModelSerializer):
                addresses = AddressSerializer(many=True)

                class Meta:
                    model = Perfil
                    fields = (
                        "id",
                        "birth_date",
                        "addresses",
                    )

                def post_save_nested_serializers(self, instance, is_created):
                    # Do something with the parent object after the creation/update of the nested objects
                    return instance

    """

    def wrapper(klass):
        original = klass.save

        def wrapped(self, *args, **kwargs):
            # Extract the nested data from the validated data
            validated_data = self.validated_data
            initial_data = self.initial_data
            nested_validated_data = {}

            post_save_specs: "List[Tuple[NestedRelationshipType, str]]" = (
                []
            )  # Nested serializers that will be saved after the parent object is saved
            pre_save_specs = (
                []
            )  # Nested serializers that will be saved before the parent object is saved
            for field_name in field_names:
                if field_name in validated_data:
                    # Store the nested data in a separate dictionary
                    validated_data.pop(field_name)
                    nested_validated_data[field_name] = initial_data[field_name]

                    # Identify type of relationship
                    relationship_type = _get_relationship_type(
                        self.Meta.model, field_name
                    )

                    if relationship_type in [
                        NestedRelationshipType.FOREIGN_KEY,
                        NestedRelationshipType.ONE_TO_ONE,
                    ]:
                        pre_save_specs.append(
                            (
                                relationship_type,
                                field_name,
                            )
                        )
                    elif relationship_type in [
                        NestedRelationshipType.REVERSE_ONE_TO_ONE,
                        NestedRelationshipType.REVERSE_FOREIGN_KEY,
                    ]:
                        post_save_specs.append(
                            (
                                relationship_type,
                                field_name,
                            )
                        )
                    else:
                        raise NotImplementedError(
                            f"Relationship type {relationship_type} is not supported yet"
                        )

            with transaction.atomic():
                pre_saved_instances = {}

                # Save the nested objects
                for relationship_type, field_name in pre_save_specs:
                    pre_save_strategy: "NestedPreSaveStrategy" = _get_pre_save_strategy(
                        relationship_type
                    )
                    instance = pre_save_strategy(
                        serializer=self,
                        field_name=field_name,
                        parent_instance=self.instance,
                        data=nested_validated_data[field_name],
                    )
                    pre_saved_instances[field_name] = instance

                # Save the parent object
                kwargs.update(pre_saved_instances)
                is_created = self.instance is None
                parent_instance = original(self, *args, **kwargs)

                # Save the nested objects
                for relationship_type, field_name in post_save_specs:
                    post_save_strategy: "NestedPostSaveStrategy" = (
                        _get_post_save_strategy(relationship_type)
                    )
                    post_save_strategy(
                        serializer=self,
                        field_name=field_name,
                        parent_instance=parent_instance,
                        data=nested_validated_data[field_name],
                    )
                parent_instance.save()

                if hasattr(self, "post_save_nested_serializers"):
                    parent_instance = self.post_save_nested_serializers(
                        instance=parent_instance, is_created=is_created
                    )

            return parent_instance

        klass.save = wrapped
        return klass

    return wrapper


class NestedListSerializer(serializers.ListSerializer):
    """Classe base para ser utilizada como "serializer_list_class" em serializers aninhados."""

    def update(self, instance, validated_data):
        objects_mapping = {object.id: object for object in instance.all()}
        data_mapping = {}
        for initial_item, validated_item in zip(self.initial_data, validated_data):
            if "id" in initial_item:
                validated_item["id"] = initial_item["id"]

            data_mapping[
                validated_item.get("id", str(uuid.uuid4())[:6])
            ] = validated_item

        ret = []

        # Create and update
        for object_id, data in data_mapping.items():
            object = objects_mapping.get(object_id, None)
            fk_parent_field_name = data.pop("fk_parent_field_name")
            if hasattr(self.child, "_validated_data"):
                delattr(self.child, "_validated_data")
            self.child.instance = object
            self.child.initial_data = data
            self.child.is_valid(raise_exception=True)
            self.child.save(**{fk_parent_field_name: data[fk_parent_field_name]})

        # Delete
        for object_id, object in objects_mapping.items():
            if object_id not in data_mapping:
                object.delete()

        return ret


class NestedRelationChoiceField(serializers.RelatedField):
    """Classe para ser utilizada em conjunto com o decorator save_nested_choice_serializers."""

    def __init__(self, **kwargs):
        """Args:
        serializer_class: Classe do serializer que será utilizado para serializar o objeto.
        serializer_params: Dicionário com parâmetros que se deseja passar ao construtor do serializer.
        queryset: Queryset que será utilizado para recuperar o objeto. Caso não seja passado, será utilizado o queryset padrão do model (.all()).

        """
        self.serializer_class = kwargs.pop("serializer_class")
        self.serializer_params = kwargs.pop("serializer_params", {})
        self.model = self.serializer_class.Meta.model
        queryset = kwargs.pop("queryset", None)
        if queryset is None:
            queryset = self.model.objects.all()
        kwargs["queryset"] = queryset
        super().__init__(**kwargs)

    def to_representation(self, value):
        return self.serializer_class(instance=value, **self.serializer_params).data

    def to_internal_value(self, data):
        if not isinstance(data, self.model):
            instance = self.model.objects.get(id=data["id"])
        else:
            instance = data
        return instance
