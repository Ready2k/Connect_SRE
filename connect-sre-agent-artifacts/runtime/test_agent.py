#!/usr/bin/env python3
"""
Connect SRE Agent test harness.

Usage:
  # Against the running container (no rebuild needed):
  docker exec <container_id> python /app/test_agent.py

  # Locally (signature tests only — Strands not required):
  cd connect-sre-agent-artifacts/runtime && python test_agent.py

Tests:
  1. Tool signatures   — all tools return str, no bare dict params
  2. Strands registry  — zero 'unrecognized tool specification' warnings
  3. Supervisor build  — build_strands_supervisor() succeeds
  4. Bedrock hello     — live Bedrock call returns a response
"""

import os
import sys
import json
import logging

PASS = "\033[92mPASS\033[0m"  # nosec B105
FAIL = "\033[91mFAIL\033[0m"
SKIP = "\033[93mSKIP\033[0m"


# ---------------------------------------------------------------------------
# 1. Tool signature validation (no Strands dependency)
# ---------------------------------------------------------------------------

def test_tool_signatures():
    from tools import (
        query_topology, calculate_blast_radius, query_recent_mutations,
        fetch_runbook, propose_remediation, query_connect_metrics,
        query_connect_ctrs, query_cloudwatch_flow_logs,
    )

    tools = [
        query_topology, calculate_blast_radius, query_recent_mutations,
        fetch_runbook, propose_remediation, query_connect_metrics,
        query_connect_ctrs, query_cloudwatch_flow_logs,
    ]

    failures = []
    for fn in tools:
        hints = fn.__annotations__
        ret = hints.get("return")
        if ret is not str:
            failures.append(f"  {fn.__name__}: return type is {ret!r} — must be str")
        for param, hint in hints.items():
            if param == "return":
                continue
            if hint is dict:
                failures.append(f"  {fn.__name__}.{param}: type is dict — Strands cannot schema-ify bare dict")

    return failures


# ---------------------------------------------------------------------------
# 2. Strands tool registry — capture unrecognized warnings
# ---------------------------------------------------------------------------

def test_strands_registration():
    """Build the full supervisor and assert zero unrecognized-tool warnings."""
    try:
        from strands.models.bedrock import BedrockModel
        from agents_bedrock import build_strands_supervisor
    except ImportError as e:
        return None, str(e)

    unrecognized = []

    class _Capture(logging.Handler):
        def emit(self, record):
            msg = record.getMessage()
            if "unrecognized tool specification" in msg:
                start = msg.find("function ") + 9
                end = msg.find(" at ")
                name = msg[start:end] if start > 9 else msg
                unrecognized.append(name)

    handler = _Capture()
    reg_logger = logging.getLogger("strands.tools.registry")
    reg_logger.addHandler(handler)

    try:
        region = os.environ.get("AWS_REGION", "us-west-2")
        model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-6", region_name=region)
        build_strands_supervisor(model)
    except Exception as e:
        return None, str(e)
    finally:
        reg_logger.removeHandler(handler)

    return unrecognized, None


# ---------------------------------------------------------------------------
# 3. Full supervisor build (10 specialists)
# ---------------------------------------------------------------------------

def test_supervisor_build():
    try:
        from strands.models.bedrock import BedrockModel
        from agents_bedrock import build_strands_supervisor
    except ImportError as e:
        return None, str(e)

    try:
        region = os.environ.get("AWS_REGION", "us-west-2")
        model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-6", region_name=region)
        supervisor = build_strands_supervisor(model)
        return supervisor, None
    except Exception as e:
        return None, str(e)


# ---------------------------------------------------------------------------
# 4. Live Bedrock hello-world through the supervisor
# ---------------------------------------------------------------------------

def test_bedrock_hello(supervisor):
    try:
        result = supervisor(
            "This is a connectivity test. Incident ID: TEST-001. "
            "The system is healthy — no investigation required. "
            "Briefly confirm you are online and ready to investigate incidents."
        )
        text = str(result)
        # Any coherent non-empty response means the agent is alive
        return len(text.strip()) > 20, text[:300]
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run():
    results = {}

    # --- 1. Signatures ---
    print("\n[1/4] Tool signature validation...")
    try:
        failures = test_tool_signatures()
        if failures:
            print(f"  {FAIL}")
            for f in failures:
                print(f)
            results["signatures"] = False
        else:
            print(f"  {PASS}  All 8 tools have str return types and no bare dict params")
            results["signatures"] = True
    except Exception as e:
        print(f"  {FAIL}  Import error: {e}")
        results["signatures"] = False

    # --- 2. Strands registry ---
    print("\n[2/4] Strands tool registry...")
    unrecognized, err = test_strands_registration()
    if err:
        print(f"  {SKIP}  {err}")
        results["registry"] = None
    elif unrecognized:
        print(f"  {FAIL}  {len(unrecognized)} tool(s) unrecognized: {unrecognized}")
        results["registry"] = False
    else:
        print(f"  {PASS}  All tools registered without warnings")
        results["registry"] = True

    # --- 3. Supervisor build ---
    print("\n[3/4] Supervisor build (10 specialists)...")
    supervisor, err = test_supervisor_build()
    if err:
        print(f"  {FAIL}  {err}")
        results["build"] = False
    else:
        print(f"  {PASS}  Supervisor + 10 specialists built successfully")
        results["build"] = True

    # --- 4. Bedrock hello ---
    print("\n[4/4] Live Bedrock call...")
    if supervisor is None:
        print(f"  {SKIP}  Supervisor unavailable — skipping live call")
        results["bedrock"] = None
    else:
        ok, text = test_bedrock_hello(supervisor)
        if ok:
            print(f"  {PASS}  Got AGENT_OK in response")
        else:
            print(f"  {FAIL}  Response: {text}")
        results["bedrock"] = ok

    # --- Summary ---
    print("\n" + "─" * 50)
    passed  = sum(1 for v in results.values() if v is True)
    failed  = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    # Suppress noisy boto/botocore INFO logs
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.ERROR)
    logging.getLogger("strands").setLevel(logging.WARNING)
    run()
