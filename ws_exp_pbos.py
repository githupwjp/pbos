import os
import subprocess as sp
import sys

for model_type in ['bos', 'pbos']:
    for target_vectors in ["google_news", "polyglot"]:
        results_dir = f"results/ws_{target_vectors}_{model_type}"
        os.makedirs(results_dir, exist_ok=True)
        log_path = os.path.join(results_dir, "demo.log")
        model_path = os.path.join(results_dir, "model.pbos")
        cmd = f"python pbos_demo.py \
            --model_path {model_path} \
            --model_type {model_type} \
            --target_vectors {target_vectors} \
        ".split()
        with sp.Popen(['/usr/bin/tee', '-a', log_path], stdin=sp.PIPE) as tee:
            sp.call(cmd, stderr=tee.stdin)
        # sp.call(cmd)