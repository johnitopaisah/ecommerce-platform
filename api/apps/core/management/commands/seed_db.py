"""
Management command: seed_db

Creates sample categories, products, and a test customer account
so you can test all endpoints immediately without manual data entry.

Usage:
    python manage.py seed_db
    python manage.py seed_db --clear   # wipe existing seed data first
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.store.models import Category, Product

User = get_user_model()

CATEGORIES = [
    {'name': 'Electronics', 'description': 'Phones, laptops, gadgets and accessories.'},
    {'name': 'Clothing', 'description': 'Men and women fashion.'},
    {'name': 'Home & Kitchen', 'description': 'Furniture, appliances and kitchenware.'},
    {'name': 'Books', 'description': 'Fiction, non-fiction, technical and educational.'},
    {'name': 'Sports & Outdoors', 'description': 'Gym equipment, outdoor gear and sportswear.'},
]

PRODUCTS = [
    # Electronics
    {
        'title': 'Wireless Bluetooth Headphones',
        'category': 'Electronics',
        'price': Decimal('79.99'),
        'discount_price': Decimal('59.99'),
        'stock_quantity': 50,
        'description': 'Over-ear noise-cancelling headphones with 30-hour battery life.',
    },
    {
        'title': 'USB-C Charging Hub 7-Port',
        'category': 'Electronics',
        'price': Decimal('34.99'),
        'stock_quantity': 120,
        'description': 'Compatible with MacBook, iPad and all USB-C laptops.',
    },
    {
        'title': 'Mechanical Keyboard TKL',
        'category': 'Electronics',
        'price': Decimal('89.00'),
        'discount_price': Decimal('74.00'),
        'stock_quantity': 30,
        'description': 'Tenkeyless mechanical keyboard with Cherry MX Red switches.',
    },
    # Clothing
    {
        'title': 'Classic White T-Shirt',
        'category': 'Clothing',
        'price': Decimal('19.99'),
        'stock_quantity': 200,
        'description': '100% organic cotton. Available in S, M, L, XL.',
    },
    {
        'title': 'Slim Fit Chinos',
        'category': 'Clothing',
        'price': Decimal('44.99'),
        'discount_price': Decimal('34.99'),
        'stock_quantity': 80,
        'description': 'Stretch-cotton slim fit chinos in navy blue.',
    },
    # Home & Kitchen
    {
        'title': 'Stainless Steel Water Bottle 1L',
        'category': 'Home & Kitchen',
        'price': Decimal('24.99'),
        'stock_quantity': 150,
        'description': 'Double-wall insulated. Keeps drinks cold 24h, hot 12h.',
    },
    {
        'title': 'Coffee Grinder Electric',
        'category': 'Home & Kitchen',
        'price': Decimal('49.99'),
        'stock_quantity': 40,
        'description': '12-cup capacity burr grinder with 17 grind settings.',
    },
    # Books
    {
        'title': 'Clean Code by Robert C. Martin',
        'category': 'Books',
        'price': Decimal('29.99'),
        'stock_quantity': 60,
        'description': 'A handbook of agile software craftsmanship.',
    },
    {
        'title': 'The Pragmatic Programmer',
        'category': 'Books',
        'price': Decimal('34.99'),
        'stock_quantity': 45,
        'description': '20th anniversary edition. From journeyman to master.',
    },
    # Sports
    {
        'title': 'Adjustable Dumbbell Set 20kg',
        'category': 'Sports & Outdoors',
        'price': Decimal('129.99'),
        'discount_price': Decimal('99.99'),
        'stock_quantity': 25,
        'description': 'Space-saving adjustable dumbbells. 5 weight settings.',
    },
    {
        'title': 'Yoga Mat Non-Slip 6mm',
        'category': 'Sports & Outdoors',
        'price': Decimal('22.99'),
        'stock_quantity': 90,
        'description': 'Eco-friendly TPE yoga mat with carrying strap.',
    },
    # Out of stock example
    {
        'title': 'Gaming Mouse Pro',
        'category': 'Electronics',
        'price': Decimal('59.99'),
        'stock_quantity': 0,
        'description': '16000 DPI optical sensor. 6 programmable buttons.',
    },
]


class Command(BaseCommand):
    help = 'Seed the database with sample categories, products and a test user.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing seed data before creating new records.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing seed data...')
            Product.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(email='customer@test.com').delete()
            User.objects.filter(email='admin@test.com').delete()
            self.stdout.write(self.style.WARNING('Cleared.'))

        # ── Categories ─────────────────────────────────────────────────────────
        self.stdout.write('Creating categories...')
        category_map = {}
        for cat_data in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                slug=slugify(cat_data['name']),
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description'],
                    'is_active': True,
                },
            )
            category_map[cat_data['name']] = cat
            status = 'created' if created else 'already exists'
            self.stdout.write(f'  Category "{cat.name}" — {status}')

        # ── Admin user ─────────────────────────────────────────────────────────
        self.stdout.write('Creating admin user...')
        admin_user, created = User.objects.get_or_create(
            email='admin@test.com',
            defaults={
                'user_name': 'admin_user',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            admin_user.set_password('Admin1234!')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(
                '  Admin user created — email: admin@test.com / password: Admin1234!'
            ))
        else:
            self.stdout.write('  Admin user already exists.')

        # ── Products ───────────────────────────────────────────────────────────
        self.stdout.write('Creating products...')
        for prod_data in PRODUCTS:
            cat = category_map[prod_data['category']]
            slug = slugify(prod_data['title'])
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'title': prod_data['title'],
                    'category': cat,
                    'created_by': admin_user,
                    'price': prod_data['price'],
                    'discount_price': prod_data.get('discount_price'),
                    'stock_quantity': prod_data['stock_quantity'],
                    'description': prod_data['description'],
                    'is_active': True,
                },
            )
            status = 'created' if created else 'already exists'
            self.stdout.write(f'  Product "{product.title}" — {status}')

        # ── Test customer ──────────────────────────────────────────────────────
        self.stdout.write('Creating test customer...')
        customer, created = User.objects.get_or_create(
            email='customer@test.com',
            defaults={
                'user_name': 'test_customer',
                'first_name': 'Test',
                'last_name': 'Customer',
                'is_active': True,
                'is_staff': False,
            },
        )
        if created:
            customer.set_password('Customer1234!')
            customer.save()
            self.stdout.write(self.style.SUCCESS(
                '  Customer created — email: customer@test.com / password: Customer1234!'
            ))
        else:
            self.stdout.write('  Test customer already exists.')

        self.stdout.write(self.style.SUCCESS('\nSeed complete!'))
        self.stdout.write('')
        self.stdout.write('Test credentials:')
        self.stdout.write('  Admin    — admin@test.com / Admin1234!')
        self.stdout.write('  Customer — customer@test.com / Customer1234!')
