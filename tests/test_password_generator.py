# SPDX-License-Identifier: GPL-3.0-only
import os
import sys

sys.path.append(os.environ["G_TEST_BUILDDIR"] + "/../")

import unittest
from gsecrets.password_generator import _satisfies_requirements


class TestStringMethods(unittest.TestCase):
    def test_delete_entry(self):
        self.assertTrue(_satisfies_requirements("A", True, False, False, False))
        self.assertTrue(_satisfies_requirements("a", False, True, False, False))
        self.assertTrue(_satisfies_requirements("1", False, False, True, False))
        self.assertTrue(_satisfies_requirements("%", False, False, False, True))
        self.assertTrue(_satisfies_requirements("%aA1", True, True, True, True))

        self.assertFalse(_satisfies_requirements("a1%", True, False, False, False))
        self.assertFalse(_satisfies_requirements("A1%", False, True, False, False))
        self.assertFalse(_satisfies_requirements("aA%", False, False, True, False))
        self.assertFalse(_satisfies_requirements("aA1", False, False, False, True))


if __name__ == "__main__":
    unittest.main()
