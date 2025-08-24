# docker_guard.py
import os, stat, pathlib, subprocess, json

def explain_and_hint():
    sock = os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock")
    if sock.startswith("unix://"):
        path = sock[len("unix://"):]
    else:
        path = "/var/run/docker.sock"

    p = pathlib.Path(path)
    hints = {"host_socket": path, "exists": p.exists(), "advice": []}

    if not p.exists():
        hints["advice"].append("Docker daemon not reachable. Start it (e.g., `sudo systemctl start docker`) or set DOCKER_HOST.")
        return hints

    st = p.stat()
    mode = stat.filemode(st.st_mode)
    hints.update({"mode": mode, "uid": st.st_uid, "gid": st.st_gid})

    # Who owns the socket group?
    try:
        import grp, pwd
        group = grp.getgrgid(st.st_gid).gr_name
        user = pwd.getpwuid(os.getuid()).pw_name
        hints["group"] = group
        hints["user"] = user
        # Is user in that group?
        groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
        primary = grp.getgrgid(os.getgid()).gr_name
        if primary not in groups:
            groups.append(primary)
        hints["user_groups"] = groups
        if group not in groups:
            hints["advice"].append(f"Add user `{user}` to group `{group}`: `sudo usermod -aG {group} {user}` then re-login.")
    except Exception:
        pass

    # Rootless hint
    xdg = os.environ.get("XDG_RUNTIME_DIR")
    if xdg and pathlib.Path(xdg, "docker.sock").exists() and path != os.path.join(xdg, "docker.sock"):
        hints["advice"].append("Rootless Docker detected. Use: export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock")

    return hints

def require_docker():
    import docker
    try:
        return docker.from_env().version()
    except Exception as e:
        info = explain_and_hint()
        raise RuntimeError("Docker not accessible",
                           {"error": str(e), "hints": info})

if __name__ == "__main__":
    try:
        v = require_docker()
        print(json.dumps({"ok": True, "version": v}, indent=2))
    except RuntimeError as err:
        print(json.dumps({"ok": False, "details": err.args[1]}, indent=2))
        raise
