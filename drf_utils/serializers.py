from rest_framework import serializers


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """A ModelSerializer that takes an additional `fields` and `exclude` argument that controls which fields should be displayed."""

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)
        exclude = kwargs.pop("exclude", [])
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)
        self.initialize_fields(self, fields, exclude)

    def initialize_fields(self, serializer, fields, exclude):
        if fields is not None:
            allowed = list(fields)
            nested_fields = []
            for field in allowed:
                if type(field) is dict:
                    nested_fields.append(field)
                    allowed.remove(field)
                if field in exclude:
                    allowed.remove(field)

            exclude = list(exclude)
            nested_exclude = []
            for field in exclude:
                if type(field) is dict:
                    nested_exclude.append(field)
                    exclude.remove(field)

            for nested in nested_fields:
                key = list(nested)[0]
                nested_serializer = serializer.fields[key]

                exclude_for_key = []
                for nested_exc in nested_exclude:
                    if key in nested_exc:
                        exclude_for_key = list(nested_exc[key])

                self.initialize_fields(nested_serializer, nested[key], exclude_for_key)
                allowed.append(key)

            fields = tuple(allowed)

            self.select_fields(serializer, fields)

        elif exclude:
            allowed = [
                field for field in list(serializer.fields) if field not in exclude
            ]
            self.select_fields(serializer, allowed)

            for field in exclude:
                if type(field) is dict:
                    key = list(field)[0]
                    nested_serializer = serializer.fields[key]
                    self.initialize_fields(nested_serializer, None, field[key])

    def select_fields(self, serializer, fields):
        allowed = set(fields)
        existing = set(serializer.fields)
        for field_name in existing - allowed:
            serializer.fields.pop(field_name)

