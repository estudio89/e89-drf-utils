from django.test import TestCase
from .models import Profile, Address, Author, Category, Book
from .serializers import ProfileSerializer, BookSerializer, BookWithAuthorsSerializer, AuthorWithProfileSerializer, ProfileWithAuthorSerializer, AddressWithProfileSerializer
import datetime as dt

class AppTest(TestCase):

    def test_nested_strategy_with_foreign_key(self):
        # Setup
        profile = Profile.objects.create(birth_date=dt.date(2023, 2, 16))
        address = Address.objects.create(
            city="city",
            state="state",
            street="street",
            number="number",
            neighborhood="neighborhood",
            profile=profile,
        )

        # Serialize model instance
        address_serializer = AddressWithProfileSerializer(address)
        data = address_serializer.data
        self.assertEqual(data["id"], address.id)
        self.assertEqual(data["city"], address.city)
        self.assertEqual(data["state"], address.state)
        self.assertEqual(data["street"], address.street)
        self.assertEqual(data["number"], address.number)
        self.assertEqual(data["neighborhood"], address.neighborhood)
        self.assertEqual(data["profile"]["id"], profile.id)
        self.assertEqual(data["profile"]["birth_date"], "2023-02-16")

        # Update model instance with new data
        new_data = {
            "id": address.id,
            "city": "new city",
            "state": "new state",
            "street": "new street",
            "number": "new number",
            "neighborhood": "new neighborhood",
            "profile": {
                "id": profile.id,
                "birth_date": "2023-02-17",
            },
        }
        address_serializer = AddressWithProfileSerializer(address, data=new_data)
        address_serializer.is_valid(raise_exception=True)
        address_serializer.save()

        # Check if model instance was updated
        address.refresh_from_db()
        self.assertEqual(address.profile_id, profile.id)
        self.assertEqual(address.city, "new city")
        self.assertEqual(address.state, "new state")
        self.assertEqual(address.street, "new street")
        self.assertEqual(address.number, "new number")
        self.assertEqual(address.neighborhood, "new neighborhood")

        # Check if nested model instance was updated
        profile.refresh_from_db()
        self.assertEqual(profile.birth_date, dt.date(2023, 2, 17))

        # Update model instance with new data and remove reference to profile
        new_data = {
            "id": address.id,
            "city": "new city",
            "state": "new state",
            "street": "new street",
            "number": "new number",
            "neighborhood": "new neighborhood",
            "profile": None,
        }
        address_serializer = AddressWithProfileSerializer(address, data=new_data)
        address_serializer.is_valid(raise_exception=True)
        address_serializer.save()

        # Check if model instance was updated
        address.refresh_from_db()
        self.assertEqual(address.profile_id, None)
        self.assertEqual(address.city, "new city")
        self.assertEqual(address.state, "new state")
        self.assertEqual(address.street, "new street")
        self.assertEqual(address.number, "new number")
        self.assertEqual(address.neighborhood, "new neighborhood")

        # Make sure profile was not deleted
        profile.refresh_from_db()
        self.assertEqual(profile.birth_date, dt.date(2023, 2, 17))


    def test_nested_strategy_with_reverse_foreign_key(self):
        # Setup
        profile = Profile.objects.create(birth_date=dt.date(2023, 2, 16))
        address = Address.objects.create(
            city="city",
            state="state",
            street="street",
            number="number",
            neighborhood="neighborhood",
            profile=profile,
        )

        # Serialize model instance
        profile_serializer = ProfileSerializer(profile)
        data = profile_serializer.data
        self.assertEqual(data["birth_date"], "2023-02-16")
        self.assertEqual(data["addresses"][0]["id"], address.id)
        self.assertEqual(data["addresses"][0]["city"], address.city)
        self.assertEqual(data["addresses"][0]["state"], address.state)
        self.assertEqual(data["addresses"][0]["street"], address.street)
        self.assertEqual(data["addresses"][0]["number"], address.number)
        self.assertEqual(data["addresses"][0]["neighborhood"], address.neighborhood)
        self.assertEqual(len(data["addresses"]), 1)


        # Update model instance with new data
        new_data = {
            "birth_date": "2023-02-16",
            "addresses": [
                {
                    "id": address.id,
                    "city": "new city",
                    "state": "new state",
                    "street": "new street",
                    "number": "new number",
                    "neighborhood": "new neighborhood",
                },
            ],
        }
        profile_serializer = ProfileSerializer(profile, data=new_data)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        # Check if model instance was updated
        profile.refresh_from_db()
        address.refresh_from_db()
        self.assertEqual(profile.birth_date, dt.date(2023, 2, 16))
        self.assertEqual(address.profile_id, profile.id)
        self.assertEqual(address.city, "new city")
        self.assertEqual(address.state, "new state")
        self.assertEqual(address.street, "new street")
        self.assertEqual(address.number, "new number")
        self.assertEqual(address.neighborhood, "new neighborhood")
        self.assertEqual(profile.addresses.count(), 1)

        # Add new address to model instance
        new_data = {
            "birth_date": "2023-02-16",
            "addresses": [
                {
                    "id": address.id,
                    "city": "new city",
                    "state": "new state",
                    "street": "new street",
                    "number": "new number",
                    "neighborhood": "new neighborhood",
                },
                {
                    "city": "new city 2",
                    "state": "new state 2",
                    "street": "new street 2",
                    "number": "new number 2",
                    "neighborhood": "new neighborhood 2",
                },
            ],
        }
        profile_serializer = ProfileSerializer(profile, data=new_data)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        # Check if model instance was updated
        profile.refresh_from_db()
        address.refresh_from_db()
        self.assertEqual(profile.birth_date, dt.date(2023, 2, 16))
        self.assertEqual(address.profile_id, profile.id)
        self.assertEqual(address.city, "new city")
        self.assertEqual(address.state, "new state")
        self.assertEqual(address.street, "new street")
        self.assertEqual(address.number, "new number")
        self.assertEqual(address.neighborhood, "new neighborhood")
        self.assertEqual(profile.addresses.count(), 2)

        # Check if new address was created
        new_address = profile.addresses.order_by("id").last()
        self.assertEqual(new_address.profile_id, profile.id)
        self.assertEqual(new_address.city, "new city 2")
        self.assertEqual(new_address.state, "new state 2")
        self.assertEqual(new_address.street, "new street 2")
        self.assertEqual(new_address.number, "new number 2")
        self.assertEqual(new_address.neighborhood, "new neighborhood 2")

        # Remove address from model instance
        new_data = {
            "birth_date": "2023-02-16",
            "addresses": [
                {
                    "id": new_address.id,
                    "city": "new city 2",
                    "state": "new state 2",
                    "street": "new street 2",
                    "number": "new number 2",
                    "neighborhood": "new neighborhood 2",
                },
            ],
        }

        profile_serializer = ProfileSerializer(profile, data=new_data)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        # Check if newer address was kept
        profile.refresh_from_db()
        new_address.refresh_from_db()
        self.assertEqual(profile.birth_date, dt.date(2023, 2, 16))
        self.assertEqual(new_address.profile_id, profile.id)
        self.assertEqual(new_address.city, "new city 2")
        self.assertEqual(new_address.state, "new state 2")
        self.assertEqual(new_address.street, "new street 2")
        self.assertEqual(new_address.number, "new number 2")
        self.assertEqual(new_address.neighborhood, "new neighborhood 2")
        self.assertEqual(profile.addresses.count(), 1)

        # Check if older address was removed
        with self.assertRaises(Address.DoesNotExist):
            address.refresh_from_db()

    def test_nested_strategy_with_one_to_one_field(self):
        author1 = Author.objects.create(name="author1")

        # Serialize model instance
        author_serializer = AuthorWithProfileSerializer(author1)
        data = author_serializer.data

        self.assertEqual(data["id"], author1.id)
        self.assertEqual(data["name"], author1.name)
        self.assertEqual(data["profile"], None)

        # Update model instance with new data
        new_data = {
            "id": author1.id,
            "name": "new author name",
            "profile": {
                "birth_date": "2023-02-16",
                "addresses": [
                    {
                        "city": "new city",
                        "state": "new state",
                        "street": "new street",
                        "number": "new number",
                        "neighborhood": "new neighborhood",
                    }
                ],
            },
        }
        author_serializer = AuthorWithProfileSerializer(author1, data=new_data)
        author_serializer.is_valid(raise_exception=True)
        author_serializer.save()

        # Check if model instance was updated
        author1.refresh_from_db()
        profile = author1.profile
        self.assertEqual(author1.name, "new author name")
        self.assertEqual(profile.birth_date, dt.date(2023, 2, 16))
        self.assertEqual(profile.addresses.count(), 1)

        # Check if new address was created
        address = profile.addresses.first()
        self.assertEqual(address.profile_id, profile.id)
        self.assertEqual(address.city, "new city")
        self.assertEqual(address.state, "new state")
        self.assertEqual(address.street, "new street")
        self.assertEqual(address.number, "new number")
        self.assertEqual(address.neighborhood, "new neighborhood")

        # Update model instance with new data
        new_data = {
            "id": author1.id,
            "name": "new author name 2",
            "profile": {
                "birth_date": "2023-02-17",
                "addresses": [
                    {
                        "id": address.id,
                        "city": "new city 2",
                        "state": "new state 2",
                        "street": "new street 2",
                        "number": "new number 2",
                        "neighborhood": "new neighborhood 2",
                    }
                ],
            },
        }
        author_serializer = AuthorWithProfileSerializer(author1, data=new_data)
        author_serializer.is_valid(raise_exception=True)
        author_serializer.save()

        # Check if model instance was updated
        author1.refresh_from_db()
        address.refresh_from_db()
        profile.refresh_from_db()
        self.assertEqual(author1.name, "new author name 2")
        self.assertEqual(profile.birth_date, dt.date(2023, 2, 17))
        self.assertEqual(profile.addresses.count(), 1)

        # Check if address was updated
        self.assertEqual(address.profile_id, profile.id)
        self.assertEqual(address.city, "new city 2")
        self.assertEqual(address.state, "new state 2")
        self.assertEqual(address.street, "new street 2")
        self.assertEqual(address.number, "new number 2")
        self.assertEqual(address.neighborhood, "new neighborhood 2")

        # Update model instance with new data and delete profile
        new_data = {
            "id": author1.id,
            "name": "new author name 3",
            "profile": None,
        }
        author_serializer = AuthorWithProfileSerializer(author1, data=new_data)
        author_serializer.is_valid(raise_exception=True)
        author_serializer.save()

        # Check if model instance was updated
        author1.refresh_from_db()
        self.assertEqual(author1.name, "new author name 3")
        self.assertEqual(author1.profile, None)

        # Check if profile was deleted
        with self.assertRaises(Profile.DoesNotExist):
            profile.refresh_from_db()


    def test_nested_strategy_with_reverse_one_to_one_field(self):
        author1 = Author.objects.create(name="author1")
        profile = Profile.objects.create(birth_date=dt.date(2020, 2, 16))

        # Serialize model instance
        profile_serializer = ProfileWithAuthorSerializer(profile)
        data = profile_serializer.data

        self.assertEqual(data["id"], profile.id)
        self.assertEqual(data["birth_date"], "2020-02-16")

        # Update model instance with new data
        new_data = {
            "id": profile.id,
            "birth_date": "2023-02-16",
            "author": {
                "id": author1.id,
                "name": "new author name",
            },
            "addresses": [
                {
                    "city": "new city",
                    "state": "new state",
                    "street": "new street",
                    "number": "new number",
                    "neighborhood": "new neighborhood",
                }
            ],
        }
        profile_serializer = ProfileWithAuthorSerializer(profile, data=new_data)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        # Check if model instance was updated
        profile.refresh_from_db()
        self.assertEqual(profile.birth_date, dt.date(2023, 2, 16))
        self.assertEqual(profile.author.name, "new author name")
        self.assertEqual(profile.addresses.count(), 1)

        # Check if new address was created
        address = profile.addresses.first()
        self.assertEqual(address.profile_id, profile.id)
        self.assertEqual(address.city, "new city")
        self.assertEqual(address.state, "new state")
        self.assertEqual(address.street, "new street")
        self.assertEqual(address.number, "new number")
        self.assertEqual(address.neighborhood, "new neighborhood")

        # Update model instance with new data
        new_data = {
            "id": profile.id,
            "birth_date": "2023-02-17",
            "author": {
                "id": author1.id,
                "name": "new author name 2",
            },
            "addresses": [
                {
                    "id": address.id,
                    "city": "new city 2",
                    "state": "new state 2",
                    "street": "new street 2",
                    "number": "new number 2",
                    "neighborhood": "new neighborhood 2",
                }
            ],
        }
        profile_serializer = ProfileWithAuthorSerializer(profile, data=new_data)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        # Check if model instance was updated
        profile.refresh_from_db()
        address.refresh_from_db()
        self.assertEqual(profile.birth_date, dt.date(2023, 2, 17))
        self.assertEqual(profile.author.name, "new author name 2")
        self.assertEqual(profile.addresses.count(), 1)

        # Check if address was updated
        self.assertEqual(address.profile_id, profile.id)
        self.assertEqual(address.city, "new city 2")
        self.assertEqual(address.state, "new state 2")
        self.assertEqual(address.street, "new street 2")
        self.assertEqual(address.number, "new number 2")
        self.assertEqual(address.neighborhood, "new neighborhood 2")


    def test_choice_strategy(self):
        category1 = Category.objects.create(name="category1")
        category2 = Category.objects.create(name="category2")

        book = Book.objects.create(title="book1", category=category1)

        # Serialize model instance
        book_serializer = BookSerializer(book)
        data = book_serializer.data

        self.assertEqual(data["id"], book.id)
        self.assertEqual(data["title"], book.title)
        self.assertEqual(data["category"]["id"], category1.id)
        self.assertEqual(data["category"]["name"], category1.name)

        # Update model instance with new data
        new_data = {
            "id": book.id,
            "title": "new book title",
            "category": {"id": category2.id, "name": category2.name},
        }
        book_serializer = BookSerializer(book, data=new_data)
        book_serializer.is_valid(raise_exception=True)
        book_serializer.save()

        # Check if model instance was updated
        book.refresh_from_db()
        category1.refresh_from_db()
        category2.refresh_from_db()
        self.assertEqual(book.title, "new book title")
        self.assertEqual(book.category_id, category2.id)
        self.assertEqual(category1.books.count(), 0)
        self.assertEqual(category2.books.count(), 1)
        self.assertEqual(category1.name, "category1")
        self.assertEqual(category2.name, "category2")

    def test_choice_strategy_with_many_to_many_field(self):
        author1 = Author.objects.create(name="author1")
        author2 = Author.objects.create(name="author2")
        category1 = Category.objects.create(name="category1")
        book = Book.objects.create(title="book1", category=category1)
        book.authors.add(author1)

        # Serialize model instance
        book_serializer = BookWithAuthorsSerializer(book)
        data = book_serializer.data

        self.assertEqual(data["id"], book.id)
        self.assertEqual(data["title"], book.title)
        self.assertEqual(data["authors"][0]["id"], author1.id)
        self.assertEqual(data["authors"][0]["name"], author1.name)
        self.assertEqual(len(data["authors"]), 1)

        # Update model instance with new data
        new_data = {
            "id": book.id,
            "title": "new book title",
            "authors": [
                {"id": author1.id, "name": author1.name},
                {"id": author2.id, "name": author2.name},
            ],
        }
        book_serializer = BookWithAuthorsSerializer(book, data=new_data)
        book_serializer.is_valid(raise_exception=True)
        book_serializer.save()

        # Check if model instance was updated
        book.refresh_from_db()
        author1.refresh_from_db()
        author2.refresh_from_db()
        self.assertEqual(book.title, "new book title")
        self.assertEqual(book.authors.count(), 2)
        self.assertEqual(author1.books.count(), 1)
        self.assertEqual(author2.books.count(), 1)
        self.assertEqual(author1.name, "author1")
        self.assertEqual(author2.name, "author2")

        # Remove author from model instance
        new_data = {
            "id": book.id,
            "title": "new book title",
            "authors": [{"id": author1.id, "name": author1.name}],
        }
        book_serializer = BookWithAuthorsSerializer(book, data=new_data)
        book_serializer.is_valid(raise_exception=True)
        book_serializer.save()

        # Check if model instance was updated
        book.refresh_from_db()
        author1.refresh_from_db()
        author2.refresh_from_db()
        self.assertEqual(book.title, "new book title")
        self.assertEqual(book.authors.count(), 1)
        self.assertEqual(author1.books.count(), 1)
        self.assertEqual(author2.books.count(), 0)
        self.assertEqual(author1.name, "author1")
        self.assertEqual(author2.name, "author2")




