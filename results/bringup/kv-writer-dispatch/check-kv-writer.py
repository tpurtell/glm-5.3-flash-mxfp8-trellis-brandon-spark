import torch
from vllm import _custom_ops as ops
from vllm.v1.attention.backends.mla.b12x_mla_sparse import B12xMLASparseImpl
from b12x.attention._shared.mla.kv_cache import concat_and_cache_nvfp4_mla_fp8_rope
x=torch.ones((2,512),device='cuda',dtype=torch.bfloat16)
rope=torch.zeros((2,1,64),device='cuda',dtype=torch.bfloat16)
slots=torch.tensor([0,1],device='cuda',dtype=torch.int64)
scale=torch.ones((),device='cuda')
try:
    ops.concat_and_cache_mla(x,rope.squeeze(1),torch.zeros((1,256,432),device='cuda',dtype=torch.uint8),slots,'nvfp4_ds_mla',scale)
except RuntimeError as e:
    print('stock writer reproduced:', str(e), flush=True)
else:
    raise AssertionError('Expected stock writer failure was not reproduced')
impl=object.__new__(B12xMLASparseImpl)
impl.rope_pad=64
impl._kv_fp8_rope=True
impl._nvfp4_dynamic_scale=True
impl._concat_and_cache_nvfp4_mla_fp8_rope=concat_and_cache_nvfp4_mla_fp8_rope
cache=torch.zeros((1,256,368),device='cuda',dtype=torch.uint8)
impl.do_kv_cache_update(x,rope,cache,slots,'nvfp4_ds_mla',scale)
torch.cuda.synchronize()
assert cache[0,:2,:256].count_nonzero().item()==512
assert cache[0,2:].count_nonzero().item()==0
print('B12X dynamic-scale backend writer: PASS (two records written, unused slots untouched)',flush=True)
