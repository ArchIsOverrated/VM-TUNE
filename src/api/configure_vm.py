import subprocess
import json

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
        Example: "/home/owner/Projects/VM-TUNE/src/core/configure_vm.sh"

    query_object : str
        The query to pass to the script via the `--query` flag.
        This determines what data is returned by the script.

        Examples:
            "vms"            -> List available virtual machines
            "cpu-topology"   -> Retrieve CPU topology information
            "presets"        -> Get available configuration presets

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
    >>> script = "/path/to/configure_vm.sh"
    >>> vms = query(script, "vms")
    >>> print(vms)

    >>> cpu = query(script, "cpu-topology")
    >>> for core in cpu:
    ...     print(core)

    """
    command = subprocess.run([script_location,"--query",query_object], capture_output=True, text=True)
    json_object = json.loads(command.stdout)
    return json_object



def action(script_location,action, **action_args):
    """
    Execute a VM-TUNE CLI action.

    Builds and runs a command like:
        configure_vm.sh --action <action> --key value ...

    Parameters
    ----------
    script_location : str
        Absolute path to the shell script to execute.
        Example: "/usr/local/lib/VMTUNE/src/core/configure_vm.sh"

    action : str
        The action to execute (e.g. "configure", "create", etc.)

    **action_args : dict
        Keyword arguments converted into CLI flags.

        Supported/Example arguments:
        - vm : str
            Name of the virtual machine
            Example: "Windows11"

        - cpu : str
            CPU cores assigned to the VM (comma-separated list)
            Example: "0,1,2,3,4,5,6,7,8,9,10,11"

        - emulator : str
            CPU cores reserved for the emulator
            Example: "12,13"

        - preset : int or str
            Preset configuration ID
            Example: 2

        - laptop : int or str
            Laptop mode toggle 0 or 1
            Example: "1"

        - libdir : str
            Path to VM-TUNE library directory
            Example: "/usr/local/lib/VMTUNE/"

        Example usage:
            action(
                "configure",
                vm="Windows11GamingVM2",
                cpu="0,1,2,3,4,5,6,7,8,9,10,11",
                emulator="12,13",
                preset=2,
                laptop="1",
                libdir="/usr/local/lib/VMTUNE/"
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
    cmd = [script_location, "--action", action]

    for k, v in action_args.items():
        print(k,v)
        cmd += [f"--{k}", str(v)]

    p = subprocess.run(cmd)

    return {"success": p.returncode == 0, "returncode": p.returncode}
