import io
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import strict_json
import configuration
import documents_index
import test_results

class StrictJsonTests(unittest.TestCase):
    def test_duplicate_and_constants(self):
        for raw in ['{"x":1,"x":2}','{"x":{"a":1,"a":2}}','[NaN]','[Infinity]','{"broken":']:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError): strict_json.read(io.StringIO(raw))

    def test_size_and_record_bound(self):
        with patch('strict_json.MAX_BYTES',16):
            with self.assertRaises(ValueError): strict_json.read(io.StringIO('"'+'中'*10+'"'))
        with self.assertRaises(ValueError): strict_json.records([None]*10001)

    def test_bad_databases_rejected_without_modification(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'data.json'
            cases=[(configuration.load,'{"schema_version":true,"parts":[]}'),
                   (documents_index.load,'{"schema_version":1.0,"documents":[]}'),
                   (test_results.load,'[{"run_id":"x","run_id":"y"}]')]
            for loader,raw in cases:
                path.write_text(raw)
                with self.assertRaises(ValueError): loader(path)
                self.assertEqual(path.read_text(),raw)

    def test_limits_and_valid_schema(self):
        for value in (True,1.0,'1',2,None):
            with self.assertRaises(ValueError): strict_json.schema(value)
        strict_json.schema(1)
        self.assertEqual(strict_json.read(io.StringIO('{"schema_version":1}')),{'schema_version':1})

if __name__=='__main__': unittest.main()
