import subprocess
import json

def query(script_location,query_object):
    command = subprocess.run([script_location,"--query",query_object], capture_output=True, text=True)
    json_object = json.loads(command.stdout)
    return json_object

def action(script_location,action, **action_args):
  cmd = [script_location, "--action", action]

  for k, v in action_args.items():
    print(k,v)
    cmd += [f"--{k}", str(v)]

  p = subprocess.run(cmd)
  if p.returncode == 0:
    success = True
  else:
    success = False

  result = {}
  result["success"] = success
  result["returncode"] = p.returncode

  return result
