from random import randint
from expiringdict import ExpiringDict
from app import  db


verify_expire_code = ExpiringDict(max_len=50, max_age_seconds=600) 

def random_gentarted(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

def save_changes(data):
    db.session.add(data)
    db.session.commit()

