import json
from vllm.utils.argparse_utils import FlexibleArgumentParser
from vllm.entrypoints.openai.cli_args import make_arg_parser
from vllm.engine.arg_utils import AsyncEngineArgs
plan=json.load(open('/plan.json'))
cmd=plan['plan'][0]['command'];i=cmd.index('glm53-trellismx-spark:dev')
argv=['--model',cmd[i+1],*cmd[i+2:],'--chat-template','/opt/trellismx/data/serving_chat_template.jinja']
args=make_arg_parser(FlexibleArgumentParser()).parse_args(argv)
config=AsyncEngineArgs.from_cli_args(args).create_engine_config()
print(json.dumps({'status':'config_created','model_architectures':config.model_config.architectures,'tp_size':config.parallel_config.tensor_parallel_size,'nnodes':config.parallel_config.nnodes,'kv_cache_dtype':config.cache_config.cache_dtype}),flush=True)
