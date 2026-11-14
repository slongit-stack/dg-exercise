import os
import unittest
from unittest.mock import patch

from scripts.run_parakeet_upstream import run_with_environment


class ExportEnvironmentTests(unittest.TestCase):
    def test_export_keeps_cache_setting_and_device_override(self):
        with patch.dict(os.environ, {'CUPY_CACHE_DIR': '/tmp/test-cupy-cache',
                                     'CUDA_VISIBLE_DEVICES': 'parent'}):
            with patch('scripts.run_parakeet_upstream.subprocess.run') as run:
                run_with_environment(['export'], check=True,
                                     env={'CUDA_VISIBLE_DEVICES': '0'})
                kwargs = run.call_args.kwargs
                self.assertEqual(kwargs['env']['CUPY_CACHE_DIR'], '/tmp/test-cupy-cache')
                self.assertEqual(kwargs['env']['CUDA_VISIBLE_DEVICES'], '0')
                self.assertTrue(kwargs['check'])

    def test_no_explicit_environment_is_left_to_subprocess(self):
        with patch('scripts.run_parakeet_upstream.subprocess.run') as run:
            run_with_environment(['export'], check=True)
            self.assertNotIn('env', run.call_args.kwargs)


if __name__ == '__main__':
    unittest.main()
