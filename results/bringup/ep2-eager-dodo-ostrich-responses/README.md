# First EP2 full-model responses

Dodo + ostrich, dense TP2 and routed EP2, eager target-only serving. Both ranks
loaded their assigned experts and completed warmup. The three basic checks
returned the correct final arithmetic answer, exactly `391` with thinking off,
and a parsed `get_weather({"city":"Taipei"})` call with thinking enabled.

The default-thinking response is not identical to TP2: it uses 325 completion
tokens versus 90, briefly computes 400 - 9 incorrectly as 396, then explicitly
corrects itself to 391. This difference is retained in the raw response; these
checks do not establish quality equivalence or a general EP2 quality score.
The thinking-off and tool function/arguments agree with TP2 on these prompts.
The tool was not executed. Full quality, graph-mode EP2, speculation and
performance qualification remain pending. Startup overlapped another pair's
loading and is not a qualified startup measurement.
