import subprocess
import json

def query(lib_dir,command,query_object):
    script_dir = lib_dir + "bin/vmtune"
    command_to_run = subprocess.run([script_dir,command, "--query", query_object], capture_output=True, text=True)
    json_object = json.loads(command_to_run.stdout)
    return json_object

def action(lib_dir,command,action, **action_args):
  script_dir = lib_dir + "bin/vmtune"
  command_to_run = [script_dir, command, "--action", action]

  for k, v in action_args.items():
    print(k,v)
    command_to_run += [f"--{k}", str(v)]

  p = subprocess.run(cmd)
  if p.returncode == 0:
    success = True
  else:
    success = False

  result = {}
  result["success"] = success
  result["returncode"] = p.returncode

  return result
