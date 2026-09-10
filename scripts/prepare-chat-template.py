#!/usr/bin/env python3
"""Preserve Z.ai's template; adapt only explicit thinking-off generation suffix."""
import hashlib
import json
from pathlib import Path
import sys


def prepare(root):
    lock = json.loads((root / 'sources.lock.json').read_text())['chat_template']
    source = (root / 'data/chat_template.jinja').read_bytes()
    if hashlib.sha256(source).hexdigest() != lock['sha256']:
        raise ValueError('Official template differs from pinned SHA256')
    text = source.decode()
    original = "<|assistant|>{{- '<think>' -}}"
    replacement = "<|assistant|>{{- '<think></think>' if enable_thinking is defined and enable_thinking == false else '<think>' -}}"
    if text.count(original) != 1:
        raise ValueError('Official generation suffix changed; review adapter')
    effective = text.replace(original, replacement).encode()
    (root / 'data/serving_chat_template.jinja').write_bytes(effective)
    receipt = dict(lock, serving_sha256=hashlib.sha256(effective).hexdigest(),
                   adaptation='explicit enable_thinking=false closes initial think span')
    (root / 'data/chat-template-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    print(json.dumps(prepare(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1])))
