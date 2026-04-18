import subprocess
import json

def query(script_location,command,query_object):
    command_to_run = subprocess.run([script_location,command, "--query", query_object], capture_output=True, text=True)
    json_object = json.loads(command_to_run.stdout)
    return json_object

def action(script_location,command,action, **action_args):
  command_to_run = [script_location, command, "--action", action]
  for k, v in action_args.items():
    print(k,v)
    command_to_run += [f"--{k}", str(v)]
  p = subprocess.run(command_to_run)
  if p.returncode == 0:
    success = True
  else:
    success = False
  result = {}
  result["success"] = success
  result["returncode"] = p.returncode

  return result
