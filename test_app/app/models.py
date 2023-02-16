from django.db import models


class Profile(models.Model):
    birth_date = models.DateField()


class Address(models.Model):
    city = models.TextField()
    state = models.TextField()
    street = models.TextField()
    number = models.TextField()
    neighborhood = models.TextField()
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="addresses", null=True
    )


class Author(models.Model):
    name = models.TextField()
    profile = models.OneToOneField(
        "Profile", on_delete=models.CASCADE, related_name="author", null=True
    )


class Category(models.Model):
    name = models.TextField()


class Book(models.Model):
    title = models.TextField()
    authors = models.ManyToManyField("Author", related_name="books")
    category = models.ForeignKey(
        "Category", on_delete=models.CASCADE, related_name="books", null=True
    )
