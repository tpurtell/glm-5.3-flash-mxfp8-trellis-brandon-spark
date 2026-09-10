# First successful TP2 full-model responses

On emu + kiwi, target-only eager serving with the corrected B12X dynamic NVFP4
cache ABI returned three valid responses:

- Default thinking: 17 × 23 = 391, with nonempty parsed reasoning.
- Explicit thinking off: exactly `391`, with null reasoning.
- Automatic tool choice: parsed `get_weather` call with `{"city":"Taipei"}`,
  nonempty reasoning, and `finish_reason: tool_calls`.

The tool call was inspected only; no weather service was invoked. These are
basic output/template/parser checks, not tool-eval scores or a performance block.
The first request included JIT compilation, so its wall time is not decode speed.
Full raw responses, client, both worker logs and launch receipt are included.
CUDA-graph serving, EP, TP4, speculation and full benchmark suites remain pending.
