#!/usr/bin/env bash
# archero.sh — One command to run the Archero 2 autoclicker.
#
# Usage:
#   ./archero.sh          # WiFi mode (default) — no cable needed
#   ./archero.sh --usb    # USB mode — phone connected via cable, uses iproxy

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USB_MODE=false
if [[ "$1" == "--usb" ]]; then
    USB_MODE=true
fi

# ── Auto-detect WDA project path ─────────────────────────────────────────────
WDA_PROJECT="$(npm root -g 2>/dev/null)/appium-webdriveragent/WebDriverAgent.xcodeproj"
if [[ ! -f "$WDA_PROJECT/project.pbxproj" ]]; then
    echo "  ❌ WebDriverAgent not found. Run: npm install -g appium-webdriveragent"
    exit 1
fi

# ── Auto-detect connected iPhone ─────────────────────────────────────────────
echo ""
echo "  Checking for connected iPhone..."
DEVICE_LINE="$(xcrun devicectl list devices 2>/dev/null | grep -i "iphone" | head -1)"
if [[ -z "$DEVICE_LINE" ]]; then
    echo "  ❌ No iPhone found. Connect your phone and trust this Mac, then try again."
    exit 1
fi
# Extract UUID by pattern (8-4-4-4-12 hex) — immune to varying phone name lengths
DEVICE_ID="$(echo "$DEVICE_LINE" | grep -oE '[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}')"
DEVICE_NAME="$(echo "$DEVICE_LINE" | awk '{print $1, $2, $3, $4}' | sed 's/ *$//')"
echo "  ✅ iPhone found: $DEVICE_NAME ($DEVICE_ID)"

# ── Cleanup on exit ──────────────────────────────────────────────────────────
IPROXY_PID=""
cleanup() {
    echo ""
    echo "  Stopping WDA..."
    kill "$WDA_PID" 2>/dev/null || true
    [[ -n "$IPROXY_PID" ]] && kill "$IPROXY_PID" 2>/dev/null || true
    wait "$WDA_PID" 2>/dev/null || true
    echo "  Done."
}
trap cleanup EXIT INT TERM

# ── Start WDA ────────────────────────────────────────────────────────────────
echo "  Starting WebDriverAgent on phone..."
xcodebuild test \
    -project "$WDA_PROJECT" \
    -scheme WebDriverAgentRunner \
    -destination "id=$DEVICE_ID" \
    -allowProvisioningUpdates \
    > /tmp/wda.log 2>&1 &
WDA_PID=$!

# ── USB mode: start iproxy and use localhost ──────────────────────────────────
if [[ "$USB_MODE" == true ]]; then
    echo "  USB mode: starting iproxy..."
    iproxy 8100 8100 > /tmp/iproxy.log 2>&1 &
    IPROXY_PID=$!
    WDA_URL="http://localhost:8100"
else
    # WiFi mode: extract phone IP from WDA log once it starts
    echo "  WiFi mode: waiting for phone IP from WDA..."
    for i in $(seq 1 180); do
        PHONE_IP="$(grep -o 'ServerURLHere->http://[^:]*' /tmp/wda.log 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1)"
        if [[ -n "$PHONE_IP" ]]; then break; fi
        if ! kill -0 "$WDA_PID" 2>/dev/null; then
            echo "  ❌ WDA crashed. Check /tmp/wda.log for details."
            exit 1
        fi
        sleep 1
    done
    if [[ -z "$PHONE_IP" ]]; then
        echo "  ❌ Could not detect phone IP. Try --usb mode."
        exit 1
    fi
    WDA_URL="http://$PHONE_IP:8100"
    echo "  Phone IP: $PHONE_IP"
fi

# ── Wait for WDA to be ready ─────────────────────────────────────────────────
echo "  Waiting for WDA to be ready..."
for i in $(seq 1 90); do
    if curl -s --max-time 1 "$WDA_URL/status" | grep -q '"ready"'; then
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
echo "  ✅ WDA ready at $WDA_URL"

# ── Launch bot ───────────────────────────────────────────────────────────────
cd "$SCRIPT_DIR"
source venv/bin/activate
WDA_URL="$WDA_URL" python bot.py
