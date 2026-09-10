import importlib.util
from pathlib import Path
import unittest

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

if __name__=='__main__':unittest.main()
