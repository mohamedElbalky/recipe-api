"""
    django command to wait for the database to be avaliable
"""

import time

from psycopg2 import OperationalError as psycopg2OpError

from django.db.utils import OperationalError
from django.core.management.base import BaseCommand

from django.db import connections


        
class Command(BaseCommand):
    """Django command to pause execution until database is available"""

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        db_conn = None
        while not db_conn:
            try:
                db_conn = connections['default']
            except OperationalError:
                self.stdout.write('Database unavailable, waiting 1 second...')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database available!'))
        
# class Command(BaseCommand):
#     """Django command to wait for database"""
    
#     def handle(self, *args, **options):
#         self.stdout.write("waiting for database...")
#         db_up = False
#         while db_up is False:
#             try:
#                 self.check(databases=['default'])
#                 # print("**********************************")
#                 # print(self.check(databases=['default']))
#                 # print("**********************************")
#                 db_up = True
#             except (psycopg2OpError, OperationalError):
#                 self.stdout.write("Database unavailable, waiting 1second...")
#                 time.sleep(1)
#         self.stdout.write(self.style.SUCCESS("Database available"))
