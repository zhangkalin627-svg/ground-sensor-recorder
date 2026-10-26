"""Concurrent output-directory protection test for pipeline_report (v0.35.0)."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import pipeline_report
from recorder import FIELDS


def make_log(path):
    rows = [','.join(FIELDS)]
    for i in range(100):
        t = i * 0.05
        rows.append(f'{t:.3f},0.1,0.2,9.81,1,2,3,101325')
    path = Path(path)
    path.write_text('\n'.join(rows) + '\n', encoding='utf-8')
    return path


class PipelineOutputConcurrencyTests(unittest.TestCase):
    def test_same_output_path_allows_only_first_concurrent_run(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = make_log(Path(d) / 'baseline.txt')
            candidate = make_log(Path(d) / 'candidate.txt')
            output = Path(d) / 'shared-run'
            first_replay_started = threading.Event()
            release_first_replay = threading.Event()
            real_import_lines = pipeline_report.replay_session.import_lines

            def pause_first_replay(source, out_dir):
                if not first_replay_started.is_set():
                    first_replay_started.set()
                    if not release_first_replay.wait(timeout=15):
                        raise TimeoutError('test did not release first replay')
                return real_import_lines(source, out_dir)

            with patch('pipeline_report.replay_session.import_lines',
                       side_effect=pause_first_replay):
                with ThreadPoolExecutor(max_workers=1) as executor:
                    first_run = executor.submit(
                        pipeline_report.build_pipeline, baseline, candidate, output)
                    try:
                        self.assertTrue(first_replay_started.wait(timeout=10))
                        with self.assertRaises(pipeline_report.PipelineFailure) as caught:
                            pipeline_report.build_pipeline(baseline, candidate, output)
                        self.assertEqual(caught.exception.stage, 'create_output_directory')
                        self.assertTrue(output.is_dir())
                        self.assertFalse((output / 'pipeline_manifest.json').exists())
                    finally:
                        release_first_replay.set()
                    first_result = first_run.result(timeout=30)

            manifest_path = first_result[3]
            self.assertEqual(manifest_path, output / 'pipeline_manifest.json')
            self.assertTrue(manifest_path.is_file())
            self.assertEqual(first_result[4]['status'], 'completed')
            self.assertTrue((output / 'baseline.json').is_file())
            self.assertTrue((output / 'candidate.json').is_file())
            self.assertTrue((output / 'drift.json').is_file())


if __name__ == '__main__':
    unittest.main()
