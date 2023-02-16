from drf_utils.nesting import (
    save_nested_serializers,
    save_nested_choice_serializers,
    NestedListSerializer,
    NestedRelationChoiceField,
)
from rest_framework.serializers import ModelSerializer
from .models import Address, Profile, Book, Author, Category


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


@save_nested_serializers(["addresses"])
class ProfileSerializer(ModelSerializer):
    addresses = AddressSerializer(many=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "birth_date",
            "addresses",
        )

    def post_save_nested_serializers(self, instance, is_created):
        # Do something after saving nested serializers
        return instance


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "id",
            "name",
        )


@save_nested_choice_serializers(["category"])
class BookSerializer(ModelSerializer):
    category = NestedRelationChoiceField(
        allow_null=False,
        serializer_class=CategorySerializer,
    )

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "category",
        )


class AuthorSerializer(ModelSerializer):
    class Meta:
        model = Author
        fields = (
            "id",
            "name",
        )


@save_nested_choice_serializers(["authors"])
class BookWithAuthorsSerializer(ModelSerializer):
    authors = NestedRelationChoiceField(
        allow_null=False,
        serializer_class=AuthorSerializer,
        many=True,
    )

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "authors",
        )


@save_nested_serializers(["profile"])
class AuthorWithProfileSerializer(ModelSerializer):
    profile = ProfileSerializer(allow_null=True)

    class Meta:
        model = Author
        fields = (
            "id",
            "name",
            "profile",
        )


@save_nested_serializers(["author", "addresses"])
class ProfileWithAuthorSerializer(ModelSerializer):
    author = AuthorSerializer()
    addresses = AddressSerializer(many=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "birth_date",
            "author",
            "addresses",
        )

class SimpleProfileSerializer(ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "id",
            "birth_date",
        )

@save_nested_serializers(["profile"])
class AddressWithProfileSerializer(ModelSerializer):
    profile = SimpleProfileSerializer(allow_null=True)

    class Meta:
        model = Address
        fields = (
            "id",
            "city",
            "state",
            "street",
            "number",
            "neighborhood",
            "profile",
        )