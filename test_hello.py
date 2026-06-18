import unittest
from hello import saludar

class TestHello(unittest.TestCase):
    def test_saludar(self):
        self.assertEqual(saludar(), "Hello World DevSecOps")

if __name__ == '__main__':
    unittest.main()