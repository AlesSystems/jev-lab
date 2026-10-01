import os
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

DEMOS = Path(__file__).resolve().parent


class EnvTests(unittest.TestCase):
    def load(self, path):
        return runpy.run_path(str(DEMOS / 'env.py'))['load_api_key'](path)

    def test_missing_file_leaves_environment_alone(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            self.load(Path(folder) / '.env')
            self.assertNotIn('TYPESAFE_API_KEY', os.environ)

    def test_reads_key_and_preserves_exported_value(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            path = Path(folder) / '.env'
            path.write_text('# local settings\nOTHER=value\nexport TYPESAFE_API_KEY = "test=key#123" # comment\n')
            self.load(path)
            self.assertEqual(os.environ['TYPESAFE_API_KEY'], 'test=key#123')
            self.assertNotIn('OTHER', os.environ)
            os.environ['TYPESAFE_API_KEY'] = 'shell-key'
            self.load(path)
            self.assertEqual(os.environ['TYPESAFE_API_KEY'], 'shell-key')
            os.environ['TYPESAFE_API_KEY'] = ''
            self.load(path)
            self.assertEqual(os.environ['TYPESAFE_API_KEY'], '')

    def test_empty_key_stays_offline_and_invalid_value_is_redacted(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            path = Path(folder) / '.env'
            for value in ('', '""', '# comment'):
                with self.subTest(value=value):
                    path.write_text('TYPESAFE_API_KEY=' + value)
                    self.load(path)
                    self.assertNotIn('TYPESAFE_API_KEY', os.environ)
            for value in ('"secret', 'secret other', 'secret\x00'):
                with self.subTest(value=value):
                    path.write_text('TYPESAFE_API_KEY=' + value)
                    with self.assertRaises(ValueError) as error:
                        self.load(path)
                    self.assertNotIn('secret', str(error.exception))

    def test_demo_commands_load_root_env_from_another_directory(self):
        harness = '''
import os, runpy, sys
script = sys.argv[1]
sys.argv = [script, '--help']
try:
    runpy.run_path(script, run_name='__main__')
except SystemExit as error:
    if error.code:
        raise
print('loaded-key=' + os.environ.get('TYPESAFE_API_KEY', ''))
'''
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '.env').write_text('TYPESAFE_API_KEY=local-test-key\n')
            (root / 'demos').mkdir()
            loader = DEMOS / 'env.py'
            if loader.exists():
                shutil.copy(loader, root / 'demos' / 'env.py')
            for source in sorted(DEMOS.glob('*/*.py')):
                if source.stem != source.parent.name or source.stem == 'demo_dashboard':
                    continue
                with self.subTest(demo=source.stem):
                    target = root / 'demos' / source.parent.name / source.name
                    target.parent.mkdir()
                    shutil.copy(source, target)
                    result = subprocess.run(
                        [sys.executable, '-c', harness, str(target)], cwd=root.parent,
                        env={key: value for key, value in os.environ.items() if key != 'TYPESAFE_API_KEY'},
                        capture_output=True, text=True, timeout=10, check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn('loaded-key=local-test-key', result.stdout)


if __name__ == '__main__':
    unittest.main()
