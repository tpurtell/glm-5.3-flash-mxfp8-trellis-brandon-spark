"""Install the P8 adapter into the pinned ARM64 vLLM ModelOpt loader."""
from pathlib import Path
import shutil
import vllm

root = Path(vllm.__file__).parent
source = Path(__file__).parent
modelopt = root / 'model_executor/layers/quantization/modelopt.py'
text = modelopt.read_text()
marker = '# Spark TrellisMX adapter hook'
if marker in text:
    raise RuntimeError('TrellisMX adapter is already installed')
generic = '        # handle kv-cache first so we can focus only on weight quantization thereafter'
mixed = '        # KV-cache quantization'
for anchor, config in ((generic, 'self'), (mixed, 'self.nvfp4_config')):
    if text.count(anchor) != 1:
        raise RuntimeError(f'Unsupported ModelOpt source: {anchor!r}')
    hook = f'''        {marker}
        if isinstance(layer, RoutedExperts):
            from .trellismx import maybe_trellismx_method
            method = maybe_trellismx_method({config}, layer, prefix)
            if method is not None:
                return method

'''
    text = text.replace(anchor, hook + anchor)
compile(text, str(modelopt), 'exec')
shutil.copy2(source / 'trellismx.py', modelopt.parent / 'trellismx.py')
shutil.copy2(source / 'trellismx_manifest.py', root / 'utils/trellismx.py')
modelopt.write_text(text)
print('Installed TrellisMX ModelOpt hooks')
