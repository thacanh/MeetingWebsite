import os
import sys

TESTS_DIR = os.path.abspath(os.path.dirname(__file__))
SERVER_DIR = os.path.abspath(os.path.join(TESTS_DIR, '..', 'source', 'server'))

if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)
