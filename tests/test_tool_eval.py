import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('toolbench',Path(__file__).resolve().parents[1]/'scripts/bench-tool-eval.py')
bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(bench)

class ToolScoreTests(unittest.TestCase):
    def inputs(self):
        plan={'scenarios':[{'id':f'TC-{i}','category':'P' if i>69 else 'A'} for i in range(1,89)]}
        result={'scores':{'scenario_results':[{'scenario_id':f'TC-{i}','points':2} for i in range(1,89)],'max_points':176,'total_points':176,'final_score':100}}
        return result,plan
    def test_original_and_hard_denominators(self):
        result,plan=self.inputs();r=bench.summarize(result,plan)
        self.assertEqual((r['original_points'],r['hard_points']),(138,38))
    def test_infrastructure_exclusion_rejected(self):
        result,plan=self.inputs();result['scores']['max_points']=174
        with self.assertRaises(ValueError):bench.summarize(result,plan)
    def test_duplicate_cannot_replace_missing_case(self):
        result,plan=self.inputs();result['scores']['scenario_results'][-1]['scenario_id']='TC-1'
        with self.assertRaises(ValueError):bench.summarize(result,plan)
    def test_model_quality_failure_kept_in_score(self):
        result,plan=self.inputs();result['scores']['scenario_results'][-1]['points']=0
        result['scores']['total_points']=174
        r=bench.summarize(result,plan)
        self.assertEqual(r['status'],'complete');self.assertEqual(r['hard_points'],36)
        self.assertEqual(len(r['failures']),1)

if __name__=='__main__':unittest.main()
