#!/usr/bin/env python3
"""
FSE workspace state management script.

Usage:
  workspace.py init <path>
  workspace.py status
  workspace.py get-state
  workspace.py set-state <STATE>
  workspace.py get-mode
  workspace.py set-mode <mode> [--scope frontend,backend]
  workspace.py set-integration-target --type own|external [--base-url <url>] [--auth-type <t>] [--auth-value <v>]
  workspace.py add-project --type frontend|backend --name <n> --path <p> --tech <t> [--start-cmd <cmd>] [--port <port>]
  workspace.py set-branch --name <n> --base <b> --feature <f> --switched true|false
  workspace.py set-startup --name <n> [--args <a>] [--env KEY=VAL ...] [--health-url <url>]
  workspace.py task-update --id <id> --status pending|in_progress|completed [--session <sid>]
  workspace.py add-issue --phase integration|testing --text <text> --severity blocking|minor
  workspace.py resolve-issue --id <issue_id>
  workspace.py progress
  workspace.py session-start
  workspace.py session-end
  workspace.py session-save [--session-id <id>] [--name <name>] [--status suspended|in_progress|completed]
  workspace.py session-list
  workspace.py session-restore --session-id <id>
  workspace.py session-update-status --session-id <id> --status suspended|in_progress|completed
  workspace.py ensure-bash-permission
  workspace.py list-test-envs
  workspace.py set-test-env --name <name> --base-url <url> --type local|remote [--tapd-project-id <id>]
  workspace.py get-test-env [--name <name>]
  workspace.py set-active-test-env --name <name>
  workspace.py add-test-account [--env <name>] --role <role> --username <u> --password <p>
  workspace.py set-test-config [--base-url <url>] [--account role:user:pass ...]
  workspace.py get-test-config
  workspace.py list-projects [--type frontend|backend]
  workspace.py check-services [--project <name>]
  workspace.py start-services [--project <name>]
  workspace.py stop-services [--project <name>]
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Force UTF-8 output on Windows (avoids UnicodeEncodeError with Chinese text)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE_DIR = ".fullstack"
WORKSPACE_FILE = ".fullstack/workspace.json"
PROGRESS_FILE = "progress.md"
SESSIONS_DIR = ".fullstack/sessions"
REGISTRY_FILE = Path.home() / ".claude" / "fse-registry.json"

VALID_MODES = ["full", "backend", "frontend", "frontend-ext", "lite"]

# Phases executed per mode (in order)
MODE_PHASES = {
    "full":         ["REQUIREMENTS", "ANALYSIS", "CONTRACT", "DEVELOPMENT", "MANUAL", "INTEGRATION", "TESTING"],
    "backend":      ["REQUIREMENTS", "ANALYSIS", "CONTRACT", "DEVELOPMENT", "MANUAL", "TESTING"],
    "frontend":     ["REQUIREMENTS", "ANALYSIS", "DEVELOPMENT", "INTEGRATION", "TESTING"],
    "frontend-ext": ["REQUIREMENTS", "ANALYSIS", "DEVELOPMENT", "INTEGRATION", "TESTING"],
    "lite":         ["REQUIREMENTS", "ANALYSIS", "DEVELOPMENT"],
}

# Scope (which project types are involved) per mode
MODE_SCOPE = {
    "full":         ["frontend", "backend"],
    "backend":      ["backend"],
    "frontend":     ["frontend"],
    "frontend-ext": ["frontend"],
    "lite":         [],  # determined at mode-selection time
}


VALID_STATES = [
    "INIT",
    "WORKSPACE_READY",
    "REQUIREMENTS_DRAFTING",
    "REQUIREMENTS_CONFIRMED",
    "ANALYSIS_IN_PROGRESS",
    "ANALYSIS_CONFIRMED",
    "CONTRACT_DEFINING",
    "CONTRACT_CONFIRMED",
    "DEVELOPMENT_IN_PROGRESS",
    "DEVELOPMENT_DONE",
    "MANUAL_TASKS_PENDING",
    "MANUAL_TASKS_DONE",
    "INTEGRATION_IN_PROGRESS",
    "INTEGRATION_PASSED",
    "TESTING_IN_PROGRESS",
    "REPORTING",
    "COMPLETED",
]

PHASE_LABELS = {
    "INIT": "初始化中",
    "WORKSPACE_READY": "就绪 — 等待需求输入",
    "REQUIREMENTS_DRAFTING": "需求：草稿中",
    "REQUIREMENTS_CONFIRMED": "需求：已确认",
    "ANALYSIS_IN_PROGRESS": "分析：进行中",
    "ANALYSIS_CONFIRMED": "分析：已确认",
    "CONTRACT_DEFINING": "API 合约：定义中",
    "CONTRACT_CONFIRMED": "API 合约：已确认",
    "DEVELOPMENT_IN_PROGRESS": "开发：进行中",
    "DEVELOPMENT_DONE": "开发：已完成",
    "MANUAL_TASKS_PENDING": "人工任务：待处理",
    "MANUAL_TASKS_DONE": "人工任务：已完成",
    "INTEGRATION_IN_PROGRESS": "联调：进行中",
    "INTEGRATION_PASSED": "联调：已通过",
    "TESTING_IN_PROGRESS": "测试：进行中",
    "REPORTING": "生成交付报告中",
    "COMPLETED": "已完成",
}


def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return {"projects": {"frontend": [], "backend": []}}
    try:
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"projects": {"frontend": [], "backend": []}}


def save_registry(data: dict):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def die(msg: str):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def load_workspace() -> dict:
    p = Path(WORKSPACE_FILE)
    if not p.exists():
        die(f"Workspace not found: {WORKSPACE_FILE}. Run 'workspace.py init <path>' first.")
    return json.loads(p.read_text(encoding="utf-8"))


def save_workspace(data: dict):
    p = Path(WORKSPACE_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def cmd_init(args):
    workspace_path = args.path or str(Path.cwd())
    ws_id = f"ws-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
    session_id = f"sess-{uuid.uuid4().hex[:8]}"

    data = {
        "workspace_id": ws_id,
        "workspace_path": workspace_path,
        "created_at": now_iso(),
        "state": "INIT",
        "current_session_id": session_id,
        "sessions": [{"id": session_id, "started_at": now_iso(), "state_at_start": "INIT"}],
        "current_feature": {
            "id": None,
            "mode": None,
            "scope": [],
            "integration_target": {
                "type": "own",
                "base_url": "",
                "auth_type": "none",
                "auth_value": "",
                "api_docs_url": "",
                "api_docs_path": "",
            },
        },
        "projects": {"frontend": [], "backend": []},
        "design_config": {
            "css_unit": "rem",
            "root_font_size": 100,
        },
        "requirements": {
            "source_type": None,
            "requirements_url": None,
            "ui_url": None,
            "user_description": None,
            "confirmed": False,
            "confirmed_at": None,
        },
        "analysis": {"confirmed": False, "confirmed_at": None},
        "contracts": {
            "path": f"{WORKSPACE_DIR}/contracts/openapi.yaml",
            "confirmed": False,
            "confirmed_at": None,
        },
        "development": {"tasks": []},
        "manual_tasks": {"confirmed": False, "items": []},
        "integration": {
            "rounds": 0,
            "max_rounds": 5,
            "backend_running": False,
            "issues": [],
        },
        "testing": {
            "rounds": 0,
            "max_rounds": 3,
            "test_cases": [],
            "issues": [],
        },
    }

    # Create directory structure
    for d in [
        f"{WORKSPACE_DIR}/requirements",
        f"{WORKSPACE_DIR}/analysis",
        f"{WORKSPACE_DIR}/contracts",
        f"{WORKSPACE_DIR}/tasks",
        f"{WORKSPACE_DIR}/issues",
        f"{WORKSPACE_DIR}/assets/screenshots",
        f"{WORKSPACE_DIR}/assets/icons",
        f"{WORKSPACE_DIR}/sessions",
    ]:
        Path(d).mkdir(parents=True, exist_ok=True)

    save_workspace(data)
    print(f"Initialized workspace: {ws_id}")
    print(f"Path: {workspace_path}")
    print(f"session_id: {session_id}")


def cmd_status(args):
    p = Path(WORKSPACE_FILE)
    if not p.exists():
        print("NOT_FOUND")
        sys.exit(1)
    data = load_workspace()
    print(f"workspace_id: {data['workspace_id']}")
    print(f"state: {data['state']}")
    print(f"phase: {PHASE_LABELS.get(data['state'], data['state'])}")
    fe = [pr["name"] for pr in data["projects"].get("frontend", [])]
    be = [pr["name"] for pr in data["projects"].get("backend", [])]
    print(f"frontend: {', '.join(fe) or 'none'}")
    print(f"backend: {', '.join(be) or 'none'}")


def cmd_get_state(args):
    data = load_workspace()
    print(data["state"])


def _auto_save_session(data: dict):
    """Upsert a session snapshot keyed by current_feature.id on every state change."""
    import shutil
    feat = data.get("current_feature", {})
    feature_id = feat.get("id")
    if not feature_id:
        return  # no feature started yet, nothing to snapshot

    session_dir = Path(SESSIONS_DIR) / feature_id
    session_dir.mkdir(parents=True, exist_ok=True)
    sf = session_dir / "session.json"

    # Preserve name and suspended status if already set by user
    existing_name = None
    existing_status = None
    if sf.exists():
        try:
            ex = json.loads(sf.read_text(encoding="utf-8"))
            existing_name = ex.get("name")
            existing_status = ex.get("status")
        except Exception:
            pass

    # Derive human-readable name from requirements description (once available)
    name = existing_name
    if not name:
        desc = data.get("requirements", {}).get("user_description", "")
        name = (desc[:60] + "…" if len(desc) > 60 else desc) if desc else feature_id

    # Status: completed when done, keep "suspended" if user explicitly set it, else in_progress
    state = data.get("state", "")
    if state == "COMPLETED":
        status = "completed"
    elif existing_status == "suspended":
        status = "suspended"
    else:
        status = "in_progress"

    session_data = {
        "session_id": feature_id,
        "name": name,
        "status": status,
        "saved_at": now_iso(),
        "current_state": state,
        "mode": feat.get("mode", ""),
        "workspace_snapshot": data,
    }
    sf.write_text(json.dumps(session_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Sync artifacts (requirements, contracts, analysis) — skip if dir not yet created
    for artifact in ("requirements", "contracts", "analysis"):
        src = Path(WORKSPACE_DIR) / artifact
        if src.exists():
            dst = session_dir / artifact
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)


def cmd_set_state(args):
    state = args.state
    if state not in VALID_STATES:
        die(f"Invalid state: {state}. Valid: {', '.join(VALID_STATES)}")
    data = load_workspace()
    data["state"] = state
    data["updated_at"] = now_iso()
    save_workspace(data)
    _write_progress(data)
    _auto_save_session(data)
    print(f"State set: {state}")


def cmd_add_project(args):
    data = load_workspace()
    project = {
        "name": args.name,
        "path": args.path,
        "tech_stack": args.tech,
        "start_cmd": args.start_cmd or "",
        "startup_args": args.startup_args or "",
        "startup_env": {},
        "health_check_url": "",
        "port": int(args.port) if args.port else None,
        "branch": {"base": "", "feature": "", "switched": False},
        "added_at": now_iso(),
    }
    ptype = args.type
    if ptype not in ("frontend", "backend"):
        die("--type must be frontend or backend")
    # Remove existing entry with same name
    data["projects"][ptype] = [
        p for p in data["projects"][ptype] if p["name"] != args.name
    ]
    data["projects"][ptype].append(project)
    save_workspace(data)
    print(f"Added {ptype} project: {args.name}")


def cmd_get_mode(args):
    data = load_workspace()
    feat = data.get("current_feature", {})
    print(f"mode:  {feat.get('mode') or 'not set'}")
    print(f"scope: {', '.join(feat.get('scope', [])) or 'not set'}")


def cmd_set_mode(args):
    mode = args.mode
    if mode not in VALID_MODES:
        die(f"Invalid mode: {mode}. Valid: {', '.join(VALID_MODES)}")
    data = load_workspace()
    feat_id = f"feat-{uuid.uuid4().hex[:8]}"
    scope = args.scope.split(",") if args.scope else MODE_SCOPE.get(mode, [])
    scope = [s.strip() for s in scope if s.strip() in ("frontend", "backend")]
    data["current_feature"] = {
        "id": feat_id,
        "mode": mode,
        "scope": scope,
        "integration_target": data.get("current_feature", {}).get("integration_target", {
            "type": "own", "base_url": "", "auth_type": "none",
            "auth_value": "", "api_docs_url": "", "api_docs_path": "",
        }),
    }
    data["state"] = "WORKSPACE_READY"
    save_workspace(data)
    _auto_save_session(data)
    print(f"Mode set: {mode}")
    print(f"Scope:    {', '.join(scope) or 'none'}")
    print(f"Phases:   {' → '.join(MODE_PHASES.get(mode, []))}")


def cmd_set_integration_target(args):
    data = load_workspace()
    target = data.setdefault("current_feature", {}).setdefault("integration_target", {})
    if args.type:
        target["type"] = args.type
    if args.base_url:
        target["base_url"] = args.base_url
    if args.auth_type:
        target["auth_type"] = args.auth_type
    if args.auth_value:
        target["auth_value"] = args.auth_value
    if args.api_docs_url:
        target["api_docs_url"] = args.api_docs_url
    if args.api_docs_path:
        target["api_docs_path"] = args.api_docs_path
    save_workspace(data)
    print(f"Integration target updated: {target['type']} @ {target.get('base_url', '')}")


def cmd_set_branch(args):
    data = load_workspace()
    found = False
    for ptype in ("frontend", "backend"):
        for proj in data["projects"][ptype]:
            if proj["name"] == args.name:
                proj["branch"] = {
                    "base": args.base,
                    "feature": args.feature,
                    "switched": args.switched.lower() == "true",
                }
                found = True
                break
    if not found:
        die(f"Project not found: {args.name}")
    save_workspace(data)
    print(f"Branch set for {args.name}: {args.feature}")


def cmd_set_startup(args):
    data = load_workspace()
    env_dict = {}
    for pair in (args.env or []):
        if "=" in pair:
            k, v = pair.split("=", 1)
            env_dict[k.strip()] = v.strip()
        else:
            die(f"--env value must be KEY=VALUE, got: {pair}")
    found = False
    for ptype in ("frontend", "backend"):
        for proj in data["projects"][ptype]:
            if proj["name"] == args.name:
                proj["startup_args"] = args.startup_args or ""
                if env_dict:
                    proj["startup_env"] = {**proj.get("startup_env", {}), **env_dict}
                elif not proj.get("startup_env"):
                    proj["startup_env"] = {}
                proj["health_check_url"] = args.health_url or ""
                found = True
                break
    if not found:
        die(f"Project not found: {args.name}")
    save_workspace(data)
    # Find the project again to show the updated values
    for ptype in ("frontend", "backend"):
        for proj in data["projects"][ptype]:
            if proj["name"] == args.name:
                print(f"Startup config set for {args.name}")
                print(f"  startup_args:    {proj.get('startup_args', '')}")
                print(f"  startup_env:     {proj.get('startup_env', {})}")
                print(f"  health_check_url:{proj.get('health_check_url', '')}")
                return


def cmd_set_design_config(args):
    data = load_workspace()
    config = data.setdefault("design_config", {"css_unit": "rem", "root_font_size": 100})
    if args.unit:
        if args.unit not in ("rem", "px"):
            die("--unit must be 'rem' or 'px'")
        config["css_unit"] = args.unit
    if args.root_font_size is not None:
        try:
            val = int(args.root_font_size)
            if val <= 0:
                die("--root-font-size must be positive")
            config["root_font_size"] = val
        except ValueError:
            die("--root-font-size must be an integer")
    save_workspace(data)
    print(f"Design config: unit={config['css_unit']}, root_font_size={config['root_font_size']}px")


def cmd_get_design_config(args):
    data = load_workspace()
    config = data.get("design_config", {"css_unit": "rem", "root_font_size": 100})
    print(f"css_unit: {config.get('css_unit', 'rem')}")
    print(f"root_font_size: {config.get('root_font_size', 100)}")


def _patch_bash_wildcard(settings_path: Path) -> bool:
    """Add Bash(*) to permissions.allow in the given settings file. Returns True if changed."""
    if settings_path.exists():
        try:
            with open(settings_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {}
    else:
        data = {}

    perms = data.setdefault("permissions", {})
    allow = perms.setdefault("allow", [])

    if "Bash(*)" in allow:
        return False  # already present

    allow.insert(0, "Bash(*)")
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return True


def cmd_ensure_bash_permission(args):
    changed = []

    # 1. User-level: ~/.claude/settings.local.json
    user_settings = Path.home() / ".claude" / "settings.local.json"
    if _patch_bash_wildcard(user_settings):
        changed.append(f"user: {user_settings}")

    # 2. Project-level: .claude/settings.local.json (in current working dir)
    project_settings = Path.cwd() / ".claude" / "settings.local.json"
    if _patch_bash_wildcard(project_settings):
        changed.append(f"project: {project_settings}")

    if changed:
        print("BASH_PERMISSION_ADDED")
        for loc in changed:
            print(f"  patched: {loc}")
    else:
        print("BASH_PERMISSION_OK")


def _migrate_test_config(tc):
    """Migrate old flat test_config to multi-environment format in-place."""
    if "environments" not in tc:
        base_url = tc.pop("base_url", "")
        accounts = tc.pop("accounts", [])
        tc["environments"] = {
            "local": {"type": "local", "base_url": base_url, "accounts": accounts}
        }
        tc.setdefault("active", "local")
    return tc


def _active_env(tc):
    """Return the active environment dict."""
    _migrate_test_config(tc)
    name = tc.get("active", "local")
    return tc["environments"].get(name, {"type": "local", "base_url": "", "accounts": []})


def cmd_set_test_config(args):
    """Legacy command — sets config on the 'local' environment."""
    data = load_workspace()
    tc = data.setdefault("test_config", {})
    _migrate_test_config(tc)
    env = tc["environments"].setdefault("local", {"type": "local", "base_url": "", "accounts": []})
    if args.base_url is not None:
        env["base_url"] = args.base_url
    for acct in (args.account or []):
        parts = acct.split(":", 2)
        if len(parts) != 3:
            die(f"--account must be in format role:username:password, got: {acct}")
        role, username, password = parts
        accounts = env.setdefault("accounts", [])
        existing = [a for a in accounts if a["role"] == role]
        if existing:
            existing[0]["username"] = username
            existing[0]["password"] = password
        else:
            accounts.append({"role": role, "username": username, "password": password})
    save_workspace(data)
    print(f"Test config (local) saved. base_url={env['base_url']}, accounts={len(env.get('accounts', []))}")


def cmd_get_test_config(args):
    """Return active environment config (backward-compatible output)."""
    data = load_workspace()
    tc = data.get("test_config", {})
    _migrate_test_config(tc)
    active = tc.get("active", "local")
    env = tc["environments"].get(active, {})
    print(f"active_environment: {active}")
    print(f"base_url: {env.get('base_url', '')}")
    accounts = env.get("accounts", [])
    if accounts:
        for a in accounts:
            print(f"account: role={a['role']} username={a['username']}")
    else:
        print("accounts: none configured")


def cmd_set_test_env(args):
    data = load_workspace()
    tc = data.setdefault("test_config", {})
    _migrate_test_config(tc)
    env = tc["environments"].setdefault(args.name, {"type": "local", "base_url": "", "accounts": []})
    if args.base_url is not None:
        env["base_url"] = args.base_url
    if args.env_type is not None:
        env["type"] = args.env_type
    if args.tapd_project_id is not None:
        env["tapd_project_id"] = args.tapd_project_id
    save_workspace(data)
    print(f"Test env '{args.name}' saved. type={env['type']}, base_url={env['base_url']}")


def cmd_get_test_env(args):
    data = load_workspace()
    tc = data.get("test_config", {})
    _migrate_test_config(tc)
    active = tc.get("active", "local")
    name = args.name if args.name else active
    env = tc["environments"].get(name, {})
    print(f"environment: {name}")
    print(f"type: {env.get('type', 'local')}")
    print(f"base_url: {env.get('base_url', '')}")
    if env.get("tapd_project_id"):
        print(f"tapd_project_id: {env['tapd_project_id']}")
    accounts = env.get("accounts", [])
    if accounts:
        for a in accounts:
            print(f"account: role={a['role']} username={a['username']}")
    else:
        print("accounts: none configured")


def cmd_set_active_test_env(args):
    data = load_workspace()
    tc = data.setdefault("test_config", {})
    _migrate_test_config(tc)
    if args.name not in tc["environments"]:
        die(f"Environment '{args.name}' not found. Run 'list-test-envs' to see available.")
    tc["active"] = args.name
    save_workspace(data)
    print(f"Active test environment: {args.name}")


def cmd_add_test_account(args):
    data = load_workspace()
    tc = data.setdefault("test_config", {})
    _migrate_test_config(tc)
    env_name = args.env or tc.get("active", "local")
    env = tc["environments"].setdefault(env_name, {"type": "local", "base_url": "", "accounts": []})
    accounts = env.setdefault("accounts", [])
    existing = [a for a in accounts if a["role"] == args.role]
    if existing:
        existing[0]["username"] = args.username
        existing[0]["password"] = args.password
    else:
        accounts.append({"role": args.role, "username": args.username, "password": args.password})
    save_workspace(data)
    print(f"Account saved: env={env_name}, role={args.role}, username={args.username}")


def cmd_list_test_envs(args):
    data = load_workspace()
    tc = data.get("test_config", {})
    _migrate_test_config(tc)
    active = tc.get("active", "local")
    envs = tc.get("environments", {})
    if not envs:
        print("No test environments configured.")
        return
    for name, env in envs.items():
        marker = " (active)" if name == active else ""
        print(f"env: {name}{marker}")
        print(f"  type: {env.get('type', 'local')}")
        print(f"  base_url: {env.get('base_url', '')}")
        if env.get("tapd_project_id"):
            print(f"  tapd_project_id: {env['tapd_project_id']}")
        print(f"  accounts: {len(env.get('accounts', []))}")


def _kill_by_port(port):
    """Kill any process listening on the given port. Cross-platform."""
    import subprocess
    if port is None:
        return
    try:
        if sys.platform == "win32":
            # netstat → find PID → taskkill
            result = subprocess.run(
                ["netstat", "-aon"], capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if f":{port} " in line and "LISTENING" in line:
                    parts = line.split()
                    if parts:
                        pid = parts[-1]
                        subprocess.run(["taskkill", "/F", "/PID", pid],
                                       capture_output=True, timeout=5)
        else:
            subprocess.run(["fuser", "-k", f"{port}/tcp"],
                           capture_output=True, timeout=5)
    except Exception:
        pass


def _detect_hot_reload(start_cmd: str) -> bool:
    keywords = ["spring-boot:run", "vite", "nodemon", "ts-node-dev", "--watch", "dev"]
    return any(kw in start_cmd for kw in keywords)


def _check_service_up(health_url: str, port, timeout: int = 3) -> bool:
    """Return True if service responds via health_url or port check."""
    import subprocess, socket
    if health_url:
        try:
            r = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                 health_url, "--max-time", str(timeout)],
                capture_output=True, text=True, timeout=timeout + 2
            )
            code = r.stdout.strip()
            return code.startswith("2") or code.startswith("3")
        except Exception:
            return False
    elif port:
        try:
            with socket.create_connection(("127.0.0.1", int(port)), timeout=timeout):
                return True
        except Exception:
            return False
    return False


def cmd_list_projects(args):
    """List all registered projects (frontend + backend) with their metadata."""
    data = load_workspace()
    types = [args.type] if args.type else ["frontend", "backend"]
    found = False
    for ptype in types:
        for proj in data["projects"].get(ptype, []):
            found = True
            print(f"type: {ptype}")
            print(f"name: {proj['name']}")
            print(f"path: {proj.get('path', '')}")
            print(f"port: {proj.get('port', 'unknown')}")
            print(f"start_cmd: {proj.get('start_cmd', '')}")
            print(f"health_url: {proj.get('health_check_url', '')}")
            print("---")
    if not found:
        print("NO_PROJECTS")


def _all_projects(data: dict, name_filter: str = None):
    """Return list of (ptype, proj) for all registered projects, optionally filtered by name."""
    result = [
        ("frontend", p) for p in data["projects"].get("frontend", [])
    ] + [
        ("backend", p) for p in data["projects"].get("backend", [])
    ]
    if name_filter:
        result = [(t, p) for t, p in result if p["name"] == name_filter]
    return result


def cmd_check_services(args):
    """Report running status of all (or one named) projects — frontend and backend."""
    data = load_workspace()
    projects = _all_projects(data, args.project)
    if not projects:
        print("NO_PROJECTS")
        return

    pids_dir = Path(WORKSPACE_DIR) / "pids"

    for ptype, proj in projects:
        name = proj["name"]
        port = proj.get("port")
        health_url = proj.get("health_check_url", "")
        pid_file = pids_dir / f"{name}.pid"
        hot_reload = _detect_hot_reload(proj.get("start_cmd", ""))

        # Check PID liveness
        pid_alive = False
        pid_val = None
        if pid_file.exists():
            try:
                pid_val = int(pid_file.read_text().strip())
                os.kill(pid_val, 0)  # 0 = check existence only
                pid_alive = True
            except Exception:
                pass

        status = "UP" if _check_service_up(health_url, port) else "DOWN"

        print(f"service: {name}")
        print(f"  type: {ptype}")
        print(f"  status: {status}")
        print(f"  port: {port or 'unknown'}")
        print(f"  health_url: {health_url or 'none'}")
        print(f"  hot_reload: {hot_reload}")
        print(f"  pid: {pid_val if pid_alive else 'none'}")
        print("---")


def cmd_start_services(args):
    """Start all (or one named) projects in the background. Kills stale processes first."""
    import subprocess
    data = load_workspace()
    projects = _all_projects(data, args.project)
    if not projects:
        die("No projects found in workspace.")

    pids_dir = Path(WORKSPACE_DIR) / "pids"
    pids_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = Path(WORKSPACE_DIR) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    for _ptype, proj in projects:
        name = proj["name"]
        path = proj.get("path", "")
        start_cmd = proj.get("start_cmd", "")
        startup_args = proj.get("startup_args", "")
        startup_env_dict = proj.get("startup_env", {})
        port = proj.get("port")

        if not start_cmd:
            print(f"SKIP: {name} — no start_cmd configured")
            continue

        # ── Kill stale process ──────────────────────────────────────────────
        pid_file = pids_dir / f"{name}.pid"
        if pid_file.exists():
            try:
                old_pid = int(pid_file.read_text().strip())
                try:
                    os.kill(old_pid, 9)
                    print(f"  Killed stale PID {old_pid} for {name}")
                except Exception:
                    pass
            except Exception:
                pass
            try:
                pid_file.unlink()
            except Exception:
                pass

        if port:
            _kill_by_port(port)

        # ── Build full command ──────────────────────────────────────────────
        full_cmd = start_cmd
        if startup_args:
            if "spring-boot:run" in start_cmd:
                full_cmd = f'{start_cmd} -Dspring-boot.run.jvmArguments="{startup_args}"'
            else:
                full_cmd = f"{start_cmd} {startup_args}"

        # ── Merge environment ───────────────────────────────────────────────
        env = {**os.environ, **{str(k): str(v) for k, v in startup_env_dict.items()}}

        # ── Launch ─────────────────────────────────────────────────────────
        log_file = logs_dir / f"{name}.log"
        try:
            with open(log_file, "w", encoding="utf-8", errors="replace") as lf:
                if sys.platform == "win32":
                    proc = subprocess.Popen(
                        full_cmd, shell=True, cwd=path,
                        stdout=lf, stderr=subprocess.STDOUT,
                        env=env,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    )
                else:
                    proc = subprocess.Popen(
                        full_cmd, shell=True, cwd=path,
                        stdout=lf, stderr=subprocess.STDOUT,
                        env=env, start_new_session=True,
                    )
            pid_file.write_text(str(proc.pid), encoding="utf-8")
            print(f"started: {name}")
            print(f"  pid: {proc.pid}")
            print(f"  cmd: {full_cmd}")
            print(f"  log: {log_file}")
            print(f"  cwd: {path}")
        except Exception as exc:
            print(f"ERROR: Failed to start {name}: {exc}")


def cmd_stop_services(args):
    """Stop all (or one named) projects using PID files or port-based kill."""
    data = load_workspace()
    projects = _all_projects(data, args.project)
    if not projects:
        die("No projects found.")

    pids_dir = Path(WORKSPACE_DIR) / "pids"

    for _ptype, proj in projects:
        name = proj["name"]
        port = proj.get("port")
        pid_file = pids_dir / f"{name}.pid"

        killed = False
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                try:
                    os.kill(pid, 9)
                    print(f"stopped: {name}  pid: {pid}")
                    killed = True
                except Exception:
                    pass
            except Exception:
                pass
            try:
                pid_file.unlink()
            except Exception:
                pass

        if not killed and port:
            _kill_by_port(port)
            print(f"stopped: {name}  method: port-kill  port: {port}")
        elif not killed:
            print(f"no-op: {name}  (no PID file, no port configured)")


def cmd_task_update(args):
    data = load_workspace()
    tasks = data["development"]["tasks"]
    for t in tasks:
        if t["id"] == args.id:
            t["status"] = args.status
            t["updated_at"] = now_iso()
            if args.session:
                t["codeagent_session"] = args.session
            save_workspace(data)
            print(f"Task {args.id} → {args.status}")
            return
    # Task not found — add it
    data["development"]["tasks"].append({
        "id": args.id,
        "status": args.status,
        "updated_at": now_iso(),
        "codeagent_session": args.session or "",
    })
    save_workspace(data)
    print(f"Task {args.id} created → {args.status}")


def cmd_add_issue(args):
    data = load_workspace()
    issue = {
        "id": f"issue-{uuid.uuid4().hex[:6]}",
        "text": args.text,
        "severity": args.severity,
        "phase": args.phase,
        "created_at": now_iso(),
        "resolved": False,
    }
    if args.phase == "integration":
        data["integration"]["issues"].append(issue)
    else:
        data["testing"]["issues"].append(issue)
    save_workspace(data)
    print(f"Issue added: {issue['id']}")


def cmd_resolve_issue(args):
    data = load_workspace()
    for phase_key in ("integration", "testing"):
        for issue in data.get(phase_key, {}).get("issues", []):
            if issue["id"] == args.id:
                issue["resolved"] = True
                issue["resolved_at"] = now_iso()
                save_workspace(data)
                print(f"Issue resolved: {args.id}")
                return
    die(f"Issue not found: {args.id}")


def cmd_session_start(args):
    data = load_workspace()
    session_id = f"sess-{uuid.uuid4().hex[:8]}"
    data["current_session_id"] = session_id
    data["sessions"].append({
        "id": session_id,
        "started_at": now_iso(),
        "state_at_start": data["state"],
    })
    save_workspace(data)
    print(f"session_id: {session_id}")


def cmd_session_end(args):
    data = load_workspace()
    sid = data.get("current_session_id")
    for s in data.get("sessions", []):
        if s["id"] == sid:
            s["ended_at"] = now_iso()
            s["state_at_end"] = data["state"]
            break
    save_workspace(data)
    print(f"Session ended: {sid}")


def cmd_session_save(args):
    """Save current workspace state as a named requirement session."""
    import shutil
    data = load_workspace()

    session_id = args.session_id or f"req-{uuid.uuid4().hex[:8]}"
    name = args.name or data.get("requirements", {}).get("user_description") or session_id
    if name and len(name) > 60:
        name = name[:60] + "…"
    status = args.status or "suspended"

    session_dir = Path(SESSIONS_DIR) / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    session_data = {
        "session_id": session_id,
        "name": name,
        "status": status,
        "saved_at": now_iso(),
        "current_state": data["state"],
        "mode": data.get("current_feature", {}).get("mode", ""),
        "workspace_snapshot": data,
    }
    (session_dir / "session.json").write_text(
        json.dumps(session_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Copy all key artifacts from .fullstack/
    for artifact_dir in ("requirements", "contracts", "analysis"):
        src = Path(WORKSPACE_DIR) / artifact_dir
        if src.exists():
            dst = session_dir / artifact_dir
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    print(f"session_id: {session_id}")
    print(f"name: {name}")
    print(f"status: {status}")
    print(f"state: {data['state']}")


def cmd_session_list(args):
    """List all saved requirement sessions."""
    sessions_dir = Path(SESSIONS_DIR)
    if not sessions_dir.exists():
        print("NO_SESSIONS")
        return

    sessions = []
    for d in sessions_dir.iterdir():
        if d.is_dir():
            sf = d / "session.json"
            if sf.exists():
                try:
                    sessions.append(json.loads(sf.read_text(encoding="utf-8")))
                except Exception:
                    pass

    if not sessions:
        print("NO_SESSIONS")
        return

    for s in sorted(sessions, key=lambda x: x.get("saved_at", ""), reverse=True):
        state_label = PHASE_LABELS.get(s.get("current_state", ""), s.get("current_state", ""))
        print(f"id: {s['session_id']}")
        print(f"name: {s.get('name', '—')}")
        print(f"status: {s.get('status', '—')}")
        print(f"state: {s.get('current_state', '—')} ({state_label})")
        print(f"mode: {s.get('mode', '—')}")
        print(f"saved_at: {s.get('saved_at', '—')}")
        print("---")


def cmd_session_restore(args):
    """Restore a saved session's workspace state."""
    import shutil
    session_dir = Path(SESSIONS_DIR) / args.session_id
    if not session_dir.exists():
        die(f"Session not found: {args.session_id}")

    sf = session_dir / "session.json"
    if not sf.exists():
        die(f"Session file missing in {session_dir}")

    session_data = json.loads(sf.read_text(encoding="utf-8"))
    snapshot = session_data.get("workspace_snapshot")
    if not snapshot:
        die("Session snapshot is empty or corrupt")

    save_workspace(snapshot)

    # Restore all artifacts (requirements, contracts, analysis)
    for artifact_dir in ("requirements", "contracts", "analysis"):
        src = session_dir / artifact_dir
        if src.exists():
            dst = Path(WORKSPACE_DIR) / artifact_dir
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    session_data["status"] = "in_progress"
    session_data["resumed_at"] = now_iso()
    sf.write_text(json.dumps(session_data, indent=2, ensure_ascii=False), encoding="utf-8")

    _write_progress(snapshot)
    print(f"restored: {args.session_id}")
    print(f"state: {snapshot['state']}")
    print(f"mode: {snapshot.get('current_feature', {}).get('mode', 'not set')}")


def cmd_session_update_status(args):
    """Update the status field of a saved session without touching workspace state."""
    sf = Path(SESSIONS_DIR) / args.session_id / "session.json"
    if not sf.exists():
        die(f"Session not found: {args.session_id}")
    session_data = json.loads(sf.read_text(encoding="utf-8"))
    session_data["status"] = args.status
    session_data["updated_at"] = now_iso()
    sf.write_text(json.dumps(session_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"session {args.session_id} status → {args.status}")


# ── Global project registry ──────────────────────────────────────────────────

def cmd_registry_list(args):
    """List all projects in the global registry, optionally filtered by type."""
    reg = load_registry()
    types = [args.type] if args.type else ["frontend", "backend"]
    found = False
    for ptype in types:
        for p in reg["projects"].get(ptype, []):
            found = True
            print(f"type: {ptype}")
            print(f"name: {p['name']}")
            print(f"path: {p['path']}")
            print(f"tech: {p.get('tech_stack', '—')}")
            print(f"port: {p.get('port', '—')}")
            print(f"start_cmd: {p.get('start_cmd', '—')}")
            print(f"last_used: {p.get('last_used', '—')}")
            print("---")
    if not found:
        print("NO_PROJECTS")


def cmd_registry_add(args):
    """Add or update a project in the global registry."""
    ptype = args.type
    if ptype not in ("frontend", "backend"):
        die("--type must be frontend or backend")
    reg = load_registry()
    projects = reg["projects"].setdefault(ptype, [])
    # Remove stale entry with same path or name
    projects[:] = [p for p in projects if p["path"] != args.path and p["name"] != args.name]
    entry = {
        "name": args.name,
        "path": args.path,
        "tech_stack": args.tech or "",
        "start_cmd": args.start_cmd or "",
        "port": int(args.port) if args.port else None,
        "startup_args": args.startup_args or "",
        "startup_env": {},
        "health_check_url": args.health_url or "",
        "last_used": now_iso(),
    }
    if args.env:
        for pair in args.env:
            if "=" in pair:
                k, v = pair.split("=", 1)
                entry["startup_env"][k.strip()] = v.strip()
    projects.append(entry)
    save_registry(reg)
    print(f"Registry: added {ptype} project '{args.name}' at {args.path}")


def cmd_registry_remove(args):
    """Remove a project from the global registry by name."""
    reg = load_registry()
    removed = False
    for ptype in ("frontend", "backend"):
        before = len(reg["projects"].get(ptype, []))
        reg["projects"][ptype] = [
            p for p in reg["projects"].get(ptype, []) if p["name"] != args.name
        ]
        if len(reg["projects"][ptype]) < before:
            removed = True
    if not removed:
        die(f"Project not found in registry: {args.name}")
    save_registry(reg)
    print(f"Registry: removed '{args.name}'")


def _state_icon(state: str, current: str) -> str:
    states = VALID_STATES
    ci = states.index(current) if current in states else 0
    si = states.index(state) if state in states else 0
    if si < ci:
        return "✅"
    elif si == ci:
        return "⏳"
    return "⬜"


def _write_progress(data: dict):
    state = data["state"]
    fe_projects = data["projects"].get("frontend", [])
    be_projects = data["projects"].get("backend", [])

    lines = [
        "# FSE 工作区进度",
        "",
        f"**工作区 ID**：{data['workspace_id']}",
        f"**阶段**：{PHASE_LABELS.get(state, state)}",
        f"**模式**：{data.get('current_feature', {}).get('mode') or '未选择'}",
        f"**范围**：{', '.join(data.get('current_feature', {}).get('scope', [])) or '—'}",
        f"**更新时间**：{now_iso()}",
        "",
        "## 项目",
    ]

    for p in fe_projects:
        branch = p.get("branch", {}).get("feature") or "—"
        lines.append(f"- **[前端]** {p['name']} `{branch}` — {p.get('tech_stack', '')}")
    for p in be_projects:
        branch = p.get("branch", {}).get("feature") or "—"
        port = p.get("port")
        port_str = f" :{port}" if port else ""
        lines.append(f"- **[后端]** {p['name']} `{branch}` — {p.get('tech_stack', '')}{port_str}")

    mode = data.get("current_feature", {}).get("mode", "full")
    phases = MODE_PHASES.get(mode, MODE_PHASES["full"])

    checklist = [
        ("WORKSPACE_READY", "工作区已初始化", True),
        ("REQUIREMENTS_CONFIRMED", "需求已确认", "REQUIREMENTS" in phases),
        ("ANALYSIS_CONFIRMED", "分析已确认", "ANALYSIS" in phases),
        ("CONTRACT_CONFIRMED", "API 合约已确认", "CONTRACT" in phases),
        ("DEVELOPMENT_DONE", "开发已完成", "DEVELOPMENT" in phases),
        ("MANUAL_TASKS_DONE", "人工任务已完成", "MANUAL" in phases),
        ("INTEGRATION_PASSED", "联调已通过", "INTEGRATION" in phases),
        ("COMPLETED", "测试已完成", "TESTING" in phases),
    ]

    lines += [
        "",
        "## 阶段清单",
    ]
    for check_state, label, included in checklist:
        if included:
            lines.append(f"{_state_icon(check_state, state)} {label}")
    lines.append("")

    # Development tasks
    tasks = data.get("development", {}).get("tasks", [])
    if tasks:
        lines.append("## 开发任务")
        for t in tasks:
            icon = {"completed": "✅", "in_progress": "⏳", "pending": "⬜"}.get(t.get("status", "pending"), "⬜")
            lines.append(f"{icon} `{t['id']}` {t.get('name', '')} [{t.get('type', '')}]")
        lines.append("")

    # Open issues
    int_issues = [i for i in data.get("integration", {}).get("issues", []) if not i.get("resolved")]
    test_issues = [i for i in data.get("testing", {}).get("issues", []) if not i.get("resolved")]
    if int_issues or test_issues:
        lines.append("## 未解决问题")
        for i in int_issues:
            lines.append(f"- [联调] [{i['severity'].upper()}] {i['text']}")
        for i in test_issues:
            lines.append(f"- [测试] [{i['severity'].upper()}] {i['text']}")
        lines.append("")

    Path(PROGRESS_FILE).write_text("\n".join(lines), encoding="utf-8")


def cmd_progress(args):
    data = load_workspace()
    _write_progress(data)
    print(f"进度已写入 {PROGRESS_FILE}")
    print(Path(PROGRESS_FILE).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="FSE workspace state manager")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("path", nargs="?", default=None)

    sub.add_parser("status")
    sub.add_parser("get-state")
    sub.add_parser("progress")
    sub.add_parser("session-start")
    sub.add_parser("session-end")

    p_ss = sub.add_parser("set-state")
    p_ss.add_argument("state")

    p_ap = sub.add_parser("add-project")
    p_ap.add_argument("--type", required=True)
    p_ap.add_argument("--name", required=True)
    p_ap.add_argument("--path", required=True)
    p_ap.add_argument("--tech", required=True)
    p_ap.add_argument("--start-cmd", default="")
    p_ap.add_argument("--startup-args", default="")
    p_ap.add_argument("--port", default=None)

    p_su = sub.add_parser("set-startup")
    p_su.add_argument("--name", required=True)
    p_su.add_argument("--args", default="", dest="startup_args")
    p_su.add_argument("--env", nargs="*", default=[],
                      help="KEY=VALUE pairs, e.g. --env NACOS_NS=dev SPRING_PROFILE=local")
    p_su.add_argument("--health-url", default="", dest="health_url")

    sub.add_parser("get-mode")

    p_sdc = sub.add_parser("set-design-config")
    p_sdc.add_argument("--unit", default=None, help="CSS unit: rem or px")
    p_sdc.add_argument("--root-font-size", default=None, dest="root_font_size",
                        help="Root font size in px (default: 100)")

    sub.add_parser("get-design-config")

    sub.add_parser("ensure-bash-permission")

    p_ste = sub.add_parser("set-test-env")
    p_ste.add_argument("--name", required=True)
    p_ste.add_argument("--base-url", default=None, dest="base_url")
    p_ste.add_argument("--type", default=None, dest="env_type", choices=["local", "remote"])
    p_ste.add_argument("--tapd-project-id", default=None, dest="tapd_project_id")

    p_gte = sub.add_parser("get-test-env")
    p_gte.add_argument("--name", default=None)

    p_sae = sub.add_parser("set-active-test-env")
    p_sae.add_argument("--name", required=True)

    p_ata = sub.add_parser("add-test-account")
    p_ata.add_argument("--env", default=None)
    p_ata.add_argument("--role", required=True)
    p_ata.add_argument("--username", required=True)
    p_ata.add_argument("--password", required=True)

    sub.add_parser("list-test-envs")

    p_stc = sub.add_parser("set-test-config")
    p_stc.add_argument("--base-url", default=None, dest="base_url",
                       help="Frontend/API base URL, e.g. http://localhost:3000")
    p_stc.add_argument("--account", nargs="*", default=[],
                       help="role:username:password, e.g. --account admin:admin@test.com:pass123")

    sub.add_parser("get-test-config")

    p_sm = sub.add_parser("set-mode")
    p_sm.add_argument("mode", choices=VALID_MODES)
    p_sm.add_argument("--scope", default="",
                      help="Comma-separated override: frontend,backend (default: derived from mode)")

    p_sit = sub.add_parser("set-integration-target")
    p_sit.add_argument("--type", choices=["own", "external"], default=None)
    p_sit.add_argument("--base-url", dest="base_url", default="")
    p_sit.add_argument("--auth-type", dest="auth_type",
                       choices=["bearer", "cookie", "none"], default=None)
    p_sit.add_argument("--auth-value", dest="auth_value", default="")
    p_sit.add_argument("--api-docs-url", dest="api_docs_url", default="")
    p_sit.add_argument("--api-docs-path", dest="api_docs_path", default="")

    p_sb = sub.add_parser("set-branch")
    p_sb.add_argument("--name", required=True)
    p_sb.add_argument("--base", required=True)
    p_sb.add_argument("--feature", required=True)
    p_sb.add_argument("--switched", required=True)

    p_tu = sub.add_parser("task-update")
    p_tu.add_argument("--id", required=True)
    p_tu.add_argument("--status", required=True)
    p_tu.add_argument("--session", default=None)

    p_ai = sub.add_parser("add-issue")
    p_ai.add_argument("--phase", required=True, choices=["integration", "testing"])
    p_ai.add_argument("--text", required=True)
    p_ai.add_argument("--severity", required=True, choices=["blocking", "minor"])

    p_ri = sub.add_parser("resolve-issue")
    p_ri.add_argument("--id", required=True)

    p_ssave = sub.add_parser("session-save")
    p_ssave.add_argument("--session-id", dest="session_id", default=None)
    p_ssave.add_argument("--name", default=None)
    p_ssave.add_argument("--status", default="suspended",
                         choices=["suspended", "in_progress", "completed"])

    sub.add_parser("session-list")

    p_srestore = sub.add_parser("session-restore")
    p_srestore.add_argument("--session-id", dest="session_id", required=True)

    p_sus = sub.add_parser("session-update-status")
    p_sus.add_argument("--session-id", dest="session_id", required=True)
    p_sus.add_argument("--status", required=True,
                       choices=["suspended", "in_progress", "completed"])

    p_rl = sub.add_parser("registry-list")
    p_rl.add_argument("--type", default=None, choices=["frontend", "backend"])

    p_ra = sub.add_parser("registry-add")
    p_ra.add_argument("--type", required=True, choices=["frontend", "backend"])
    p_ra.add_argument("--name", required=True)
    p_ra.add_argument("--path", required=True)
    p_ra.add_argument("--tech", default="")
    p_ra.add_argument("--start-cmd", dest="start_cmd", default="")
    p_ra.add_argument("--port", default=None)
    p_ra.add_argument("--startup-args", dest="startup_args", default="")
    p_ra.add_argument("--env", nargs="*", default=[])
    p_ra.add_argument("--health-url", dest="health_url", default="")

    p_rr = sub.add_parser("registry-remove")
    p_rr.add_argument("--name", required=True)

    p_lp = sub.add_parser("list-projects")
    p_lp.add_argument("--type", default=None, choices=["frontend", "backend"])

    p_cs = sub.add_parser("check-services")
    p_cs.add_argument("--project", default=None)

    p_sts = sub.add_parser("start-services")
    p_sts.add_argument("--project", default=None)

    p_stos = sub.add_parser("stop-services")
    p_stos.add_argument("--project", default=None)

    args = parser.parse_args()

    dispatch = {
        "init": cmd_init,
        "status": cmd_status,
        "get-state": cmd_get_state,
        "set-state": cmd_set_state,
        "add-project": cmd_add_project,
        "get-mode": cmd_get_mode,
        "set-mode": cmd_set_mode,
        "set-integration-target": cmd_set_integration_target,
        "set-branch": cmd_set_branch,
        "set-startup": cmd_set_startup,
        "set-design-config": cmd_set_design_config,
        "get-design-config": cmd_get_design_config,
        "ensure-bash-permission": cmd_ensure_bash_permission,
        "set-test-env": cmd_set_test_env,
        "get-test-env": cmd_get_test_env,
        "set-active-test-env": cmd_set_active_test_env,
        "add-test-account": cmd_add_test_account,
        "list-test-envs": cmd_list_test_envs,
        "set-test-config": cmd_set_test_config,
        "get-test-config": cmd_get_test_config,
        "task-update": cmd_task_update,
        "add-issue": cmd_add_issue,
        "resolve-issue": cmd_resolve_issue,
        "progress": cmd_progress,
        "session-start": cmd_session_start,
        "session-end": cmd_session_end,
        "session-save": cmd_session_save,
        "session-list": cmd_session_list,
        "session-restore": cmd_session_restore,
        "session-update-status": cmd_session_update_status,
        "registry-list": cmd_registry_list,
        "registry-add": cmd_registry_add,
        "registry-remove": cmd_registry_remove,
        "list-projects": cmd_list_projects,
        "check-services": cmd_check_services,
        "start-services": cmd_start_services,
        "stop-services": cmd_stop_services,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
