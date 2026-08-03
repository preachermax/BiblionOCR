import unittest
suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_myboxer_line_spacing')
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
