import os, subprocess
# fully detached start (own session, no inherited fds): a dropped client call cannot take the job down
cmd = os.environ['CMD']; log = os.environ.get('LOG', '/content/bg.log')
subprocess.Popen(['setsid', '-f', 'bash', '-c', f'{cmd} > {log} 2>&1 < /dev/null'], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True)
print('started', cmd, '->', log)
