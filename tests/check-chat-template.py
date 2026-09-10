#!/usr/bin/env python3
"""Render official template with the same Transformers Jinja engine as vLLM."""
import hashlib
import json
from pathlib import Path
from transformers.utils.chat_template_utils import _compile_jinja_template

root = Path(__file__).resolve().parents[1]
source = (root / 'data/chat_template.jinja').read_bytes()
lock = json.loads((root / 'sources.lock.json').read_text())['chat_template']
assert hashlib.sha256(source).hexdigest() == lock['sha256']
template = _compile_jinja_template(source.decode())
def render(messages, **kwargs):
    return template.render(messages=messages, tools=[], add_generation_prompt=True, **kwargs)

plain = render([{'role': 'user', 'content': 'Hello'}])
assert '<|user|>Hello' in plain and plain.endswith('<|assistant|><think>')
null = render([{'role': 'user', 'content': 'Go'}, {'role': 'assistant', 'content': None,
    'tool_calls': [{'id':'call_a', 'type':'function', 'function': {'name':'lookup', 'arguments': {'key':'x'}}}]},
    {'role':'tool', 'tool_call_id':'call_a', 'content':'found'}])
assert 'None' not in null and '<tool_call>lookup' in null and '<tool_response>found</tool_response>' in null
ordered = render([{'role':'user', 'content':'Go'}, {'role':'assistant', 'content':None,
    'tool_calls':[{'id':i, 'function':{'name':'lookup','arguments':{'key':i}}} for i in ('a','b')]},
    {'role':'tool','tool_call_id':'b','content':'RESULT_B'},
    {'role':'tool','tool_call_id':'a','content':'RESULT_A'}])
assert ordered.index('RESULT_A') < ordered.index('RESULT_B')
image = render([{'role':'user','content':[{'type':'text','text':'Describe'},
                                          {'type':'image_url','image_url':{'url':'test'}}]}])
assert '<|begin_of_image|><|image|><|end_of_image|>' in image
# Detect this limitation explicitly; matched thinking-off benchmarks must not
# silently assume that a template kwarg disables reasoning in this revision.
off = render([{'role':'user','content':'Hello'}], enable_thinking=False)
assert off == plain
print(json.dumps({'status':'passed', 'sha256':lock['sha256'],
                  'cases':['plain','null_tool_content','tool_result_order','image_placeholder'],
                  'enable_thinking_false_honored':False}))

effective = _compile_jinja_template((root / 'data/serving_chat_template.jinja').read_text())
for messages in ([{'role':'user','content':'Hello'}],
                 [{'role':'user','content':'Go'}, {'role':'assistant','content':None,
                   'tool_calls':[{'id':'a','function':{'name':'lookup','arguments':{}}}]},
                  {'role':'tool','tool_call_id':'a','content':'OK'}]):
    kwargs = dict(messages=messages, tools=[], add_generation_prompt=True)
    assert effective.render(**kwargs) == template.render(**kwargs)
    assert effective.render(**kwargs, enable_thinking=True) == template.render(**kwargs)
    disabled = effective.render(**kwargs, enable_thinking=False)
    assert disabled == template.render(**kwargs) + '</think>'
print(json.dumps({'serving_adapter':'passed', 'default_matches_official':True,
                  'explicit_thinking_off_suffix':'<think></think>'}))
