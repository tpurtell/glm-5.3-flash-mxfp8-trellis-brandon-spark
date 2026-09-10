# Chat template audit — September 10, 2026

The carrier at its pinned revision includes an older template. Brandon's base
and September 9 reference launch scripts contain no chat-template override.

| Source | SHA256 |
|---|---|
| Pinned carrier | `34d5ee66b12fa6446cdae131c352b8f68cd85369e0e6fda115583805fada3891` |
| Current official Z.ai | `0c4099f3382d6c92700dfb99725025360966fd73032f0ecf32377c0d9e6309c5` |
| Serving adapter | `74ec8ee7258eec437936bfc4669a7227c02e5f9a6f349d88d01770360bea1564` |

Official source: [zai-org/GLM-5.3-Flash at eb9eb208](https://huggingface.co/zai-org/GLM-5.3-Flash/blob/eb9eb208eb0d988989d07a6a12d0fdeb5f52574a/chat_template.jinja).
The revision was resolved through Hugging Face's model API before downloading.
Compared with the carrier, it changes null-content rendering, tool-name string
concatenation and early exits in tool-response sorting. The ARM64 base recipe's
bundled official template already matches these bytes, but this recipe's original
entrypoint bypassed that base's template preparation. The new entrypoint passes
an explicit `--chat-template` path.

`data/chat_template.jinja` preserves the official file byte-for-byte, with its MIT
license. `scripts/prepare-chat-template.py` verifies the upstream hash and derives
`data/serving_chat_template.jinja`. Its sole change is the generation suffix:
an explicit `enable_thinking=false` emits `<think></think>` instead of `<think>`.
The official template ignores that kwarg. Default and thinking-enabled renders
remain identical to official output. This is a local serving adaptation, not
presented as an upstream Z.ai change.

`tests/check-chat-template.py` uses the installed Transformers Jinja engine to
check ordinary chat, null assistant content with tool calls, reordered tool
responses, image markers, upstream identity, and the explicit thinking-off
suffix. These rendering checks passed. Full-server parser/output checks remain
part of model bring-up before running thinking-off performance comparisons.

All benchmark receipts must record the serving-template hash. Updating the
upstream pin requires regenerating the adapter and repeating these checks;
benchmark launches do not silently fetch a changing template.
