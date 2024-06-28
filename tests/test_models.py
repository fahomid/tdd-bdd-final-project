# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal, InvalidOperation
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

class TestProductBase(unittest.TestCase):
    """Base class for Product Model Test Cases"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

class TestProductModelCRUD(TestProductBase):
    """Test Cases for Product Model CRUD operations"""

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(
            name="Fedora", description="A red hat", price=Decimal(12.50),
            available=True, category=Category.CLOTHS
        )
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, Decimal(12.50))
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(new_product.price, product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_create_a_product_with_id_reset(self):
        """It should reset ID to None before creating a product"""
        product = ProductFactory()
        product.id = 999  # Assign an arbitrary ID
        product.create()  # Should reset ID to None and then create
        self.assertIsNotNone(product.id)
        self.assertNotEqual(product.id, 999)  # Ensure ID has been reset and reassigned

        # Check that the product was added to the database
        found_product = Product.find(product.id)
        self.assertIsNotNone(found_product)
        self.assertEqual(found_product.id, product.id)

    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "testing")

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        self.assertEqual(products, [])
        for _ in range(5):
            product = ProductFactory()
            product.create()
        products = Product.all()
        self.assertEqual(len(products), 5)

class TestProductModelQueries(TestProductBase):
    """Test Cases for Product Model Query operations"""

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        count = len([product for product in products if product.name == name])
        found = Product.find_by_name(name).all()
        self.assertEqual(len(found), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available).all()
        self.assertEqual(len(found), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category).all()
        self.assertEqual(len(found), count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_find_by_category_unknown(self):
        """It should Find Products by Unknown Category"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.category = Category.UNKNOWN  # Explicitly set to UNKNOWN
            product.create()
        found = Product.find_by_category(Category.UNKNOWN).all()
        self.assertEqual(len(found), 5)

    def test_find_by_price(self):
        """It should Find Products by Price"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        price = products[0].price
        count = len([product for product in products if product.price == price])
        found = Product.find_by_price(price).all()
        self.assertEqual(len(found), count)
        for product in found:
            self.assertEqual(product.price, price)

    def test_find_by_name_not_found(self):
        """It should return an empty list if no products found by name"""
        found = Product.find_by_name("nonexistent").all()
        self.assertEqual(found, [])

    def test_find_by_price_not_found(self):
        """It should return an empty list if no products found by price"""
        found = Product.find_by_price(Decimal('999.99')).all()
        self.assertEqual(found, [])

    def test_find_by_availability_not_found(self):
        """It should return an empty list if no products found by availability"""
        found = Product.find_by_availability(False).all()
        self.assertEqual(found, [])

    def test_find_by_price_string(self):
        """It should Find Products by Price given as a string"""
        product = ProductFactory(price=Decimal("19.99"))
        product.create()
        found = Product.find_by_price("19.99").all()
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].price, Decimal("19.99"))

class TestProductModelDeserialization(TestProductBase):
    """Test Cases for Product Model Deserialization"""

    def test_deserialize_missing_attribute(self):
        """It should raise an error if deserializing a product with missing attributes"""
        product = Product()
        data = {"name": "test", "price": "10.00"}
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

    def test_deserialize_invalid_price(self):
        """It should raise an error if deserializing a product with an invalid price"""
        product = Product()
        data = {
            "name": "test", "description": "test", "price": "invalid",
            "available": True, "category": "CLOTHS"
        }
        with self.assertRaises(DataValidationError):
            try:
                product.deserialize(data)
            except InvalidOperation as error:
                raise DataValidationError("Invalid price") from error

    def test_deserialize_invalid_available(self):
        """It should raise an error if deserializing a product with an invalid available type"""
        product = Product()
        data = {
            "name": "test", "description": "test", "price": "10.00",
            "available": "yes", "category": "CLOTHS"
        }
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

    def test_deserialize_invalid_category(self):
        """It should raise an error if deserializing a product with an invalid category"""
        product = Product()
        data = {
            "name": "test", "description": "test", "price": "10.00",
            "available": True, "category": "INVALID"
        }
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

class TestProductModelMisc(TestProductBase):
    """Miscellaneous Test Cases for Product Model"""

    def test_update_product_without_id(self):
        """It should not Update a Product without an ID"""
        product = ProductFactory()
        product.id = None
        with self.assertRaises(DataValidationError):
            product.update()

    def test_create_product_id_none(self):
        """It should reset ID to None and create the product"""
        product = Product(
            name="Fedora", description="A red hat", price=Decimal(12.50),
            available=True, category=Category.CLOTHS
        )
        product.id = 123  # Manually set an ID to simulate pre-existing condition
        product.create()
        self.assertIsNotNone(product.id)
        self.assertNotEqual(product.id, 123)

if __name__ == "__main__":
    unittest.main()
