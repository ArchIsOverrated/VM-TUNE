import api_utility

def query(script_location,query_object):
  """
  Execute a query against a VM-TUNE shell script and return the result as a Python object.

  This function acts as a bridge between the Python layer (GUI/API) and the
  underlying Bash-based VM-TUNE CLI. It invokes the script with a `--query`
  argument, captures the JSON output, and converts it into a Python object.

  Parameters
  ----------
  script_location : str
      Absolute path to the shell script to execute.
      Example: "/usr/local/lib/VMTUNE/src/core/install_looking-glass.sh.sh"

  query_object : str
      The query to pass to the script via the `--query` flag.
      This determines what data is returned by the script.

      Examples:
          "status"       -> Retrieve installation status
          "build-exist"   -> Looks for a build folder
          "dependencies" -> Querys dependencies to install looking-glass

  Returns
  -------
  dict or list
      Parsed JSON output from the script. The exact type depends on what the
      script returns..

  Notes
  -----
  - This function is intentionally stateless and does not retain any data
    between calls.
  - It assumes the script prints valid JSON to stdout.
  - stderr is captured but not currently handled.

  Example
  -------
  >>> script = "/path/to/install_looking-glass.sh"
  >>> looking_glass = query(script, "status")
  >>> print(looking_glass)


  """
  json_object = api_utility.query(script_location,query_object)
  return json_object

def action(action, **action_args):
  """
  Execute a VM-TUNE Looking Glass CLI action.

  Builds and runs a command like:
      install_looking-glass.sh --action <action> --key value ...

  Parameters
  ----------
  script_location : str
      Absolute path to the shell script to execute.
      Example: "/usr/local/lib/VMTUNE/src/core/configure_vm.sh"

  action : str
      The action to execute.

      Supported actions:
      - "build"         -> Build Looking Glass from source
      - "install"       -> Install Looking Glass
      - "cleanup"       -> Remove build artifacts / temporary files
      - "full-install"  -> Perform full build + install process

  **action_args : dict
      Keyword arguments converted into CLI flags.
      (Not used in current examples, but supported for extensibility)

      Example usage:
          action("build")
          action("install")
          action("cleanup")
          action("full-install")

  Returns
  -------
  dict
      {
          "success": bool,       # True if return code == 0
          "returncode": int      # Process exit code
      }

  Notes
  -----
  - Success/failure is determined ONLY by exit code.
  - No stdout/stderr or JSON parsing is performed.
  - Stateless: simply runs a command and returns status.
  """
  result = api_utility.action(script_location,action,**action_args)
  return result
