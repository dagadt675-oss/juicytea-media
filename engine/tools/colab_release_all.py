"""Release every active Colab assignment on the signed-in account (stops compute-unit billing).

Why: after a container restart the Colab CLI's local ~/.config/colab-cli/sessions.json is empty, so
`colab stop -s <name>` only prints "not found" and the VM stays assigned. This asks the backend for the
real assignment list and unassigns each one through the CLI's own client.

Run with the Colab CLI's venv python, isolated:  <colabvenv>/bin/python -I engine/tools/colab_release_all.py
Prints endpoint names and the usage rate only, never tokens.
"""
from colab_cli.common import state

c = state.client
eps = [a.endpoint for a in c.list_assignments()]
print("before:", eps)
for ep in eps:
    try:
        c.unassign(ep)
        print("unassigned:", ep)
    except Exception as e:  # keep going; report the failure without request details
        print("failed:", ep, type(e).__name__)
left = [a.endpoint for a in c.list_assignments()]
info = c.get_consumption_user_info()
print("after:", left, "| rate per hour:", getattr(info, "consumption_rate_hourly", "?"),
      "| assignments:", getattr(info, "assignments_count", "?"))
