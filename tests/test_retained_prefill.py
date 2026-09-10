import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import io
import json
import sys
import tempfile
import types

spec=importlib.util.spec_from_file_location('bench',Path(__file__).resolve().parents[1]/'scripts/bench-retained-prefill.py')
bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(bench)

class RetainedTests(unittest.TestCase):
    def result(self, cached=32768, total=33792):
        return {'usage':{'prompt_tokens':total,'prompt_tokens_details':{'cached_tokens':cached}},'ttft_seconds':2}
    def test_exact_shape(self):
        self.assertEqual(bench.validate_cell(self.result(),32768,1024,1)['new_tokens_per_second'],1024)
    def test_cache_eviction_rejected(self):
        with self.assertRaises(ValueError): bench.validate_cell(self.result(cached=32512),32768,1024,1)
    def test_hybrid_block_accounts_for_recomputed_tail(self):
        cell=bench.validate_cell(self.result(cached=30720),32768,1024,2,6144)
        self.assertEqual(cell['recomputed_base_tokens'],2048)
        self.assertEqual(cell['computed_tokens'],3072)
        self.assertEqual(cell['new_tokens_per_second'],512)
        self.assertEqual(cell['computed_tokens_per_second'],1536)
    def test_hybrid_cache_loss_is_not_hidden_by_rounding(self):
        with self.assertRaises(ValueError):
            bench.validate_cell(self.result(cached=24576),32768,1024,2,6144)
    def test_excess_reuse_rejected(self):
        with self.assertRaises(ValueError): bench.validate_cell(self.result(cached=33024),32768,1024,1)
    def test_missing_cache_detail_rejected(self):
        r=self.result();del r['usage']['prompt_tokens_details']
        with self.assertRaises(ValueError): bench.validate_cell(r,32768,1024,1)
    def test_metrics_not_histogram_buckets(self):
        raw='vllm:request_prefill_time_seconds_sum{model_name="target"} 3.5\nvllm:request_prefill_time_seconds_count{model_name="target"} 2\nvllm:request_prefill_time_seconds_bucket{le="1"} 1\n'
        self.assertEqual(bench.timing_totals(raw)[bench.PREFILL+'_sum'],3.5)
    def test_missing_metrics_rejected(self):
        with self.assertRaises(ValueError): bench.timing_totals('')

    def test_explicit_mtp_drop_accounts_for_recomputation(self):
        for base, cached in ((32768,24576),(65536,55296),(131072,122880)):
            cell=bench.validate_cell(self.result(cached,base+1024),base,1024,2,6144,1)
            self.assertEqual(cell['recomputed_base_tokens'],base-cached)
            self.assertEqual(cell['computed_tokens'],base+1024-cached)
        self.assertEqual(bench.expected_cached_tokens(0,6144,1),0)

    def test_explicit_mtp_policy_still_rejects_wrong_cache(self):
        for cached in (18432,30720):
            with self.assertRaises(ValueError):
                bench.validate_cell(self.result(cached),32768,1024,2,6144,1)
        with self.assertRaises(ValueError): bench.expected_cached_tokens(32768,6144,2)

    def test_rejected_prime_preserves_remaining_cells(self):
        class Tokenizer:
            @staticmethod
            def from_file(path): return Tokenizer()
            def encode(self, text, **kwargs): return types.SimpleNamespace(ids=list(text.encode()))
        class Template:
            def render(self, **kwargs): return 'UNIQUE_BENCH_CORPUS_SENTINEL'
        modules = {
            'tokenizers': types.SimpleNamespace(Tokenizer=Tokenizer),
            'transformers.utils.chat_template_utils': types.SimpleNamespace(
                _compile_jinja_template=lambda source: Template()),
        }
        count = 0
        def stream(url, body, *args):
            nonlocal count
            if len(body['prompt']) > 256:
                return {'error': 'HTTP Error 400', 'http_status': 400,
                        'http_error_body': 'maximum context length exceeded'}
            count += 1
            return self.result(cached=0, total=256)
        def open_url(url, **kwargs):
            data = (json.dumps({'data':[{'id':'test'}]}) if url.endswith('/v1/models') else
                    f'vllm:request_prefill_time_seconds_sum {count}\n'
                    f'vllm:request_prefill_time_seconds_count {count}\n')
            return io.BytesIO(data.encode())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'tokenizer.json').write_text('{}')
            (root/'launch.json').write_text('{}')
            argv = ['bench', '--tokenizer', str(root/'tokenizer.json'),
                    '--launch-receipt', str(root/'launch.json'), '--corpus-root', tmp,
                    '--out', str(root/'out'), '--bases', '0', '256',
                    '--suffixes', '256', '--runs', '1']
            with patch.dict(sys.modules, modules), patch.object(sys, 'argv', argv), \
                 patch.object(bench, 'corpus_tokens', return_value=([1], 'test')), \
                 patch.object(bench.client, 'stream_request', side_effect=stream), \
                 patch.object(bench.urllib.request, 'urlopen', side_effect=open_url), \
                 patch('builtins.print'):
                with self.assertRaises(SystemExit): bench.main()
            receipt = json.loads((root/'out/receipt.json').read_text())
            self.assertEqual([s['status'] for s in receipt['samples']], ['passed', 'failed'])
            self.assertEqual(receipt['status'], 'failed')
            rejected = json.loads((root/'out/base-256-suffix-256-r0.json').read_text())
            self.assertEqual(rejected['http_status'], 400)
            self.assertIn('Base priming failed', receipt['samples'][1]['error'])

if __name__=='__main__':unittest.main()
