import importlib.util
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
import unittest

spec=importlib.util.spec_from_file_location('mia',Path(__file__).resolve().parents[1]/'scripts/bench-mia-style.py')
mia=importlib.util.module_from_spec(spec);spec.loader.exec_module(mia)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        prompt=body['messages'][0]['content'] if 'messages' in body else 'completion'
        self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
        chunks=['OK'] if prompt=='single' else ['a','b','c']
        for text in chunks:
            data={'choices':[{'delta':{'content':text}}] if 'messages' in body else [{'text':text}]}
            self.wfile.write(('data: '+json.dumps(data)+'\n\n').encode());self.wfile.flush();time.sleep(.005)
        if prompt!='missing':
            self.wfile.write(('data: '+json.dumps({'choices':[],'usage':{'prompt_tokens':100,'completion_tokens':19}})+'\n\n').encode())
        self.wfile.write(b'data: [DONE]\n\n');self.wfile.flush()

class BenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def test_completions_usage(self):
        result=mia.stream_request(self.base,{'prompt':[1,2,3]},'/v1/completions')
        self.assertNotIn('error',result)
        self.assertEqual(result['text'],'abc')
        self.assertEqual(result['decode_tokens'],18)
    def test_usage_not_chunk_count(self):
        result=mia.stream(self.base,'test','multiple',400)
        self.assertNotIn('error',result)
        self.assertEqual(result['decode_tokens'],18)
        self.assertEqual(result['text'],'abc')
        self.assertAlmostEqual(result['decode_tps']*(result['last']-result['first']),18)
    def test_missing_usage_fails(self):
        self.assertIn('error',mia.stream(self.base,'test','missing',400))
    def test_single_content_prefill_is_valid(self):
        result=mia.stream(self.base,'test','single',8,False)
        self.assertNotIn('error',result);self.assertIsNone(result['decode_tps'])
        self.assertGreater(result['prefill_tps'],0)
    def test_aggregate_uses_shared_window(self):
        results=[dict(decode_tps=10,ttft_seconds=1,decode_tokens=20,first=1,last=3),
                 dict(decode_tps=20,ttft_seconds=2,decode_tokens=40,first=2,last=4)]
        self.assertEqual(mia.wave_summary(results)['aggregate_tps'],20)
        self.assertEqual(mia.wave_summary([*results,{'error':'failed'}])['status'],'failed')

if __name__=='__main__':unittest.main()
