import json
from vllm.utils.argparse_utils import FlexibleArgumentParser
from vllm.entrypoints.openai.cli_args import make_arg_parser
from vllm.engine.arg_utils import AsyncEngineArgs
plans=json.load(open('/plans.json'))
for name,plan in plans.items():
 cmd=plan['plan'][0]['command'];i=cmd.index('glm53-trellismx-spark:dev')
 argv=['--model',cmd[i+1],*cmd[i+2:],'--chat-template','/opt/trellismx/data/serving_chat_template.jinja']
 args=make_arg_parser(FlexibleArgumentParser()).parse_args(argv)
 config=AsyncEngineArgs.from_cli_args(args).create_engine_config()
 print(json.dumps({'candidate':name,'status':'config_created','tp_size':config.parallel_config.tensor_parallel_size,'nnodes':config.parallel_config.nnodes,'ep':config.parallel_config.enable_expert_parallel,'speculation':str(config.speculative_config)}),flush=True)
