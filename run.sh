#!/usr/bin/env bash
# run.sh — Plug in your iPhone and run this. That's it.
#
# Starts WDA on the phone, forwards the port, then launches the bot.
# Stop everything with Ctrl+C.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WDA_PROJECT="/Users/tigershi/.nvm/versions/node/v24.14.0/lib/node_modules/appium-webdriveragent/WebDriverAgent.xcodeproj"
DEVICE_ID="6840900E-4B5C-5227-83FC-C6807F032E03"
WDA_URL="http://localhost:8100"

# ── Cleanup on exit ──────────────────────────────────────────────────────────
cleanup() {
    echo ""
    echo "  Stopping WDA and iproxy..."
    kill "$WDA_PID" "$IPROXY_PID" 2>/dev/null || true
    wait "$WDA_PID" "$IPROXY_PID" 2>/dev/null || true
    echo "  Done."
}
trap cleanup EXIT INT TERM

# ── Check phone is connected ─────────────────────────────────────────────────
echo ""
echo "  Checking for connected iPhone..."
if ! xcrun devicectl list devices 2>/dev/null | grep -q "$DEVICE_ID"; then
    echo "  ❌ iPhone not found. Plug it in and trust this Mac, then try again."
    exit 1
fi
echo "  ✅ iPhone found."

# ── Start WDA ────────────────────────────────────────────────────────────────
echo "  Starting WebDriverAgent on phone..."
xcodebuild test \
    -project "$WDA_PROJECT" \
    -scheme WebDriverAgentRunner \
    -destination "id=$DEVICE_ID" \
    > /tmp/wda.log 2>&1 &
WDA_PID=$!

# ── Start iproxy ─────────────────────────────────────────────────────────────
echo "  Starting port forward (iproxy 8100)..."
iproxy 8100 8100 > /tmp/iproxy.log 2>&1 &
IPROXY_PID=$!

# ── Wait for WDA to be ready ─────────────────────────────────────────────────
echo "  Waiting for WDA to start (this takes ~15s)..."
for i in $(seq 1 40); do
    if curl -s --max-time 1 "$WDA_URL/status" | grep -q '"ready" : true'; then
        break
    fi
    if ! kill -0 "$WDA_PID" 2>/dev/null; then
        echo "  ❌ WDA crashed. Check /tmp/wda.log for details."
        exit 1
    fi
    sleep 1
done

if ! curl -s --max-time 1 "$WDA_URL/status" | grep -q '"ready"'; then
    echo "  ❌ WDA did not start in time. Check /tmp/wda.log"
    exit 1
fi
echo "  ✅ WDA ready."

# ── Launch bot ───────────────────────────────────────────────────────────────
cd "$SCRIPT_DIR"
source venv/bin/activate
python bot.py
