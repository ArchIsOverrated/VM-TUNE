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
      Example: "/home/owner/Projects/VM-TUNE/src/core/create_vm.sh"

  query_object : str
      The query to pass to the script via the `--query` flag.
      This determines what data is returned by the script.

      Examples:
          "isos"          -> Retrieve ISOS available on system.
          "os-variants"   -> Retrieve OS variants you can choose
          "defaults"      -> Get default CPU ram configuration

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
  >>> script = "/path/to/create_vm.sh"
  >>> isos = query(script, "isos")
  >>> print(isos)


  """
  json_object = api_utility.query(script_location,query_object)
  return json_object

def action(action, **action_args):
  """
  Execute a VM-TUNE create VM CLI action.

  Builds and runs a command like:
      create_vm.sh --action <action> --key value ...

  Parameters
  ----------
  script_location : str
  Absolute path to the shell script to execute.
  Example: "/usr/local/lib/VMTUNE/src/core/configure_vm.sh"

  action : str
      The action to execute (e.g. "create")

  **action_args : dict
      Keyword arguments converted into CLI flags.

      Supported/Example arguments:
      - vm : str
          Name of the virtual machine
          Example: "alpine"

      - iso : str
          Path to the ISO file used for installation
          Example: "/var/lib/libvirt/images/alpine-standard-3.23.2-x86_64.iso"

      - disk : str or int
          Disk size (likely in GB)
          Example: "10"

      - ram : int
          Amount of RAM in MB
          Example: 1024

      - cpu : str or int
          Number of CPU cores
          Example: "2"

      - osvariant : str
          OS variant used by libvirt
          Example: "alpinelinux3.23"

      Example usage:
          action(
              "create",
              vm="alpine",
              iso="/var/lib/libvirt/images/alpine-standard-3.23.2-x86_64.iso",
              disk="10",
              ram=1024,
              cpu="2",
              osvariant="alpinelinux3.23"
          )

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
