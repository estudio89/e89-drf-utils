import base64
import mimetypes
import uuid
from typing import Optional, cast

import six
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.fields import SkipField, empty


class WritableSerializerMethodField(serializers.Field):
    """A SerializerMethodField that also allows deserialization.

    The containing serializer must implement two methods:

        def get_{field_name}(self, instance): # for serialization
            ...

        def save_{field_name}(self, data): # for deserialization
            # data is the value of the field in the request
            # return the value to be set on the model instance
            ...

    """

    def __init__(self, method_name=None, save_method_name=None, **kwargs):
        self.method_name = method_name
        self.save_method_name = save_method_name
        kwargs["read_only"] = False
        super().__init__(**kwargs)

    def bind(self, field_name, parent):
        # In order to enforce a consistent style, we error if a redundant
        # 'method_name' argument has been used. For example:
        # my_field = serializer.SerializerMethodField(method_name='get_my_field')
        default_method_name = "get_{field_name}".format(field_name=field_name)
        default_save_method_name = "save_{field_name}".format(field_name=field_name)

        # The method name should default to `get_{field_name}`.
        if self.method_name is None:
            self.method_name = default_method_name

        if self.save_method_name is None:
            self.save_method_name = default_save_method_name

        super().bind(field_name, parent)

    def to_representation(self, value):
        method = getattr(self.parent, cast("str", self.method_name))
        return method(value)

    def to_internal_value(self, data):
        method = getattr(self.parent, cast("str", self.save_method_name))
        return method(data)

    def get_attribute(self, instance):
        return instance


class Base64FileField(serializers.FileField):
    """A FileField that accepts base64 encoded data.

    The field expects a dict with the following structure:
        {
            "data": "base64 encoded file data",
            "name": "file name" (optional)
        }

    The field will return a dict with the following structure:
        {
            "url": "absolute url to the file"
        }

    """

    def _get_content_file_from_base64_string_or_none(
        self, base64_str: "str", name: "Optional[str]" = None
    ) -> "Optional[ContentFile]":
        if isinstance(base64_str, six.string_types):
            if "data:" in base64_str and ";base64," in base64_str:
                header, base64_str = base64_str.split(";base64,")
            else:
                raise ValueError(
                    "Invalid base64 string. It should contain 'data:' and ';base64,'."
                )

            try:
                decoded_file = base64.b64decode(base64_str)
            except TypeError:
                raise ValueError(
                    "_get_content_file_from_base64_string_or_none: invalid file."
                )

            if name is None:
                file_name = str(uuid.uuid4())[:12]
                file_extension = mimetypes.guess_extension(header.replace("data:", ""))
                if file_extension is None:
                    file_extension = ".bin"
                complete_file_name = file_name + file_extension
            else:
                complete_file_name = name
            return ContentFile(decoded_file, name=complete_file_name)
        else:
            return None

    def to_representation(self, value):
        empty_response = {"url": None}
        if not value:
            return empty_response

        try:
            url = value.url
        except AttributeError:
            return empty_response

        request = self.context.get("request", None)
        if request is not None:
            url = request.build_absolute_uri(url)
        return {"url": url}

    def to_internal_value(self, data):
        file = self._get_content_file_from_base64_string_or_none(
            base64_str=data["data"], name=data.get("name")
        )
        return file

    def validate_empty_values(self, data):
        if data is empty or not data.get("data"):
            raise SkipField()
        return super().validate_empty_values(data)
