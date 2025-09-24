# test_app.py
from app import say_hello

def test_say_hello():
    assert say_hello() == "Hello, World!"
