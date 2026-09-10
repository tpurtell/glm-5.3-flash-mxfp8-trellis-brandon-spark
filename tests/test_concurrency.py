import importlib.util
from pathlib import Path
import sys
import unittest

scripts=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(scripts))
spec=importlib.util.spec_from_file_location('bench_concurrency',scripts/'bench-concurrency.py')
bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(bench)

class ConcurrencyTests(unittest.TestCase):
    def results(self):
        return [dict(start=0,end=4,first=1,last=3,decode_tokens=20,decode_tps=10,
                    ttft_seconds=1,usage={'completion_tokens':21,'prompt_tokens_details':{'cached_tokens':0}},
                    output_check={'quality_contract_passed':False}),
                dict(start=0,end=5,first=2,last=4,decode_tokens=20,decode_tps=10,
                    ttft_seconds=2,usage={'completion_tokens':21,'prompt_tokens_details':{'cached_tokens':0}},
                    output_check={'quality_contract_passed':True})]
    def test_common_window_and_makespan_are_separate(self):
        result=bench.summarize(self.results())
        self.assertAlmostEqual(result['aggregate_tps'],40/3)
        self.assertAlmostEqual(result['end_to_end_aggregate_tps'],42/5)
        self.assertEqual(result['output_checks_passed'],1)
        self.assertEqual(result['status'],'passed')
    def test_reused_prefix_invalidates_wave(self):
        results=self.results();results[0]['usage']['prompt_tokens_details']['cached_tokens']=256
        self.assertEqual(bench.summarize(results)['status'],'failed')
    def test_missing_usage_detail_is_not_assumed_cold(self):
        results=self.results();del results[0]['usage']['prompt_tokens_details']
        self.assertEqual(bench.summarize(results)['status'],'failed')
    def test_transport_failure_cannot_be_dropped(self):
        results=self.results();results[0]['error']='timeout'
        self.assertEqual(bench.summarize(results)['status'],'failed')

if __name__=='__main__':unittest.main()
