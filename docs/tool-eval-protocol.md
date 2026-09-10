# Tool evaluation protocol

`scripts/bench-tool-eval.py` requires `tool-eval-bench`
`2.6.1.dev45+gcf54b4bfe`, Git commit
`cf54b4bfe705f12f71e8866f10730572497c8105` from
[SeraphimSerapis/tool-eval-bench](https://github.com/SeraphimSerapis/tool-eval-bench).
It verifies both the reported version and installed VCS metadata. These match
the pinned GLMRT reference's evaluator.

Each topology runs all 88 scenarios serially with hard mode, temperature zero,
and thinking explicitly enabled. The three default seeds are 2026091001,
2026091002 and 2026091003. The fixed reference date remains 2026-09-08 so dated
fixtures use the same calendar as the reference; the seeds are distinct new
trials. The dry-run selection must resolve 69 original and 19 hard cases.

Every completed seed reports original points /138, hard points /38 and total
points /176, alongside the evaluator's displayed score. A run missing a case,
duplicating a case or excluding infrastructure failures is incomplete. It cannot
contribute a median with a reduced denominator. Model-quality failures remain
in the score and all failing/partial scenario records are retained.

The wrapper saves exact commands, evaluator installation/source identity,
scenario selection, launch/template receipts, full JSON results, stdout/stderr,
and evaluator artifacts. It does not enable throughput plugins or other
unrequested benchmark suites.

```bash
python3 scripts/bench-tool-eval.py \
  --launch-receipt .work/launches/ACTUAL_LAUNCH.json \
  --out results/2x/tool-eval
```

`--plan-only` verifies installation and constructs all three commands without
contacting the model. This passed against the installed pinned evaluator with
88 selected cases. Actual tool-call/parser behavior and all three measured
seeds remain pending full-model bring-up.
