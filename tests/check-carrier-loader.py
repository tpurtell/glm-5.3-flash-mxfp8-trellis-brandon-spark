#!/usr/bin/env python3
"""Exercise the installed vLLM carrier scale loader with the actual adapter type."""
import json
import torch
from vllm.model_executor.layers.fused_moe.routed_experts import RoutedExperts
from vllm.model_executor.layers.quantization.trellismx import ModelOptTrellisMXMoEMethod

layer = RoutedExperts.__new__(RoutedExperts)
torch.nn.Module.__init__(layer)
layer.quant_config = None
layer.quant_method = ModelOptTrellisMXMoEMethod.__new__(ModelOptTrellisMXMoEMethod)
layer.quant_method.use_global_sf = False
layer._map_global_expert_id_to_local_expert_id = lambda expert_id: expert_id
for name in ('w13_input_scale', 'w13_weight_scale_2'):
    parameter = torch.nn.Parameter(torch.zeros(2, 2), requires_grad=False)
    for shard, value in (('w1', 2.0), ('w3', 3.0)):
        layer.weight_loader(parameter, torch.tensor(value), name, shard, 0)
    torch.testing.assert_close(parameter, torch.tensor([[2.0,3.0],[0.0,0.0]]), rtol=0, atol=0)
    print(json.dumps({'parameter':name,'values':parameter.tolist(),'status':'passed'}))
print(json.dumps({'status':'passed','scope':'actual vLLM ModelOpt scalar/input-scale dispatch'}))
