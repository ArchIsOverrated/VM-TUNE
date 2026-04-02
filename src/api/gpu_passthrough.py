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
        Example: "/usr/local/lib/VMTUNE/src/core/gpu_passthrough.sh"

    query_object : str
        The query to pass to the script via the `--query` flag.
        This determines what data is returned by the script.

        Examples:
            "gpus"         -> Retrieve a list of GPUS on your system
            "cpu-vendor"   -> Gets cpu vendor
            "iommu-status" -> Gets status of iommu

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
    >>> script = "/path/to/gpu_passthrough.sh"
    >>> gpus = query(script, "gpus")
    >>> print(gpus)


    """
    command = subprocess.run([script_location,"--query",query_object], capture_output=True, text=True)
    json_object = json.loads(command.stdout)
    return json_object

def action(action, **action_args):
    """
    Execute a VM-TUNE GPU passthrough CLI action.

    Builds and runs a command like:
        gpu_passthrough.sh --action <action> --key value ...

    Parameters
    ----------
    script_location : str
        Absolute path to the shell script to execute.
        Example: "/usr/local/lib/VMTUNE/src/core/configure_vm.sh"

    action : str
        The action to execute (e.g. "set")

    **action_args : dict
        Keyword arguments converted into CLI flags.

        Supported/Example arguments:
        - vfio : str or int
            Enable or disable VFIO binding (likely 0 or 1)
            Example: "1"

        - gpuids : str
            Comma-separated list of GPU PCI IDs to passthrough
            Example: "10de:28e0,10de:22be"

        Example usage:
            action(
                "set",
                vfio="1",
                gpuids="10de:28e0,10de:22be"
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

