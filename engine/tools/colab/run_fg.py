import os, subprocess
print(subprocess.run(os.environ['CMD'], shell=True, capture_output=True, text=True, timeout=float(os.environ.get('T', '600'))).stdout[-6000:])
