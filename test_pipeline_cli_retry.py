"""CLI coverage for the pipeline input-change retry message (v0.37.0)."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pipeline_report
from test_pipeline_cli import make_log, run


class PipelineInputChangeCliTests(unittest.TestCase):
    def test_cli_retry_prompt_when_input_identity_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = make_log(root / 'baseline.txt')
            candidate = make_log(root / 'candidate.txt')
            output = root / 'changed-input-run'
            real_identity = pipeline_report.file_identity
            baseline_calls = [0]

            def identity_with_changed_baseline(path):
                identity = real_identity(path)
                if Path(path) == baseline:
                    baseline_calls[0] += 1
                    if baseline_calls[0] == 2:
                        identity = {**identity, 'sha256': '0' * 64}
                return identity

            with patch('pipeline_report.file_identity',
                       side_effect=identity_with_changed_baseline):
                rc, _, err = run(pipeline_report.main,
                                 [baseline, candidate, '--out', output])

            self.assertEqual(rc, 1)
            self.assertIn('阶段 verify_inputs', err)
            self.assertIn(
                '输入文件在流程运行期间发生变化；请检查后使用新输出目录重跑', err)
            self.assertTrue((output / 'pipeline_manifest.json').is_file())


if __name__ == '__main__':
    unittest.main()
