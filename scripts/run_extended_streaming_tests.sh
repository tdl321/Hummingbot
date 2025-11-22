#!/bin/bash
# Extended Exchange Streaming Comparison Test Runner
# This script runs both WebSocket and HTTP streaming tests side-by-side

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUMMINGBOT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║         Extended Exchange Streaming Tests - Side-by-Side Runner           ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if .env exists
if [ ! -f "$HUMMINGBOT_ROOT/.env" ]; then
    echo "❌ Error: .env file not found at $HUMMINGBOT_ROOT/.env"
    echo "Please create .env with EXTENDED_API_KEY"
    exit 1
fi

# Check if required Python packages are installed
echo "📦 Checking dependencies..."
python3 -c "import websockets, aiohttp, dotenv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Missing dependencies. Installing..."
    pip install websockets aiohttp python-dotenv
fi

echo "✅ Dependencies OK"
echo ""

# Function to run test with tmux
run_with_tmux() {
    if command -v tmux &> /dev/null; then
        echo "🚀 Running tests in tmux split-pane mode..."
        echo "   Press Ctrl+C in any pane to stop both tests"
        echo ""

        # Create new tmux session with split panes
        tmux new-session -d -s extended_tests
        tmux split-window -h -t extended_tests

        # Run WebSocket test in left pane
        tmux send-keys -t extended_tests:0.0 "cd $HUMMINGBOT_ROOT && python scripts/test_extended_websocket.py" C-m

        # Run HTTP streaming test in right pane
        tmux send-keys -t extended_tests:0.1 "cd $HUMMINGBOT_ROOT && python scripts/test_extended_http_stream.py" C-m

        # Attach to session
        tmux attach-session -t extended_tests
    else
        run_sequential
    fi
}

# Function to run tests sequentially
run_sequential() {
    echo "📝 Running tests sequentially (tmux not available)..."
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo "Test 1/2: WebSocket Streaming"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo ""

    cd "$HUMMINGBOT_ROOT"
    python scripts/test_extended_websocket.py

    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo "Test 2/2: HTTP Streaming (SSE)"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo ""

    python scripts/test_extended_http_stream.py
}

# Ask user for preference
echo "How would you like to run the tests?"
echo ""
echo "1) Side-by-side with tmux (recommended)"
echo "2) Sequential (one after another)"
echo "3) WebSocket only"
echo "4) HTTP streaming only"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        run_with_tmux
        ;;
    2)
        run_sequential
        ;;
    3)
        echo ""
        echo "═══════════════════════════════════════════════════════════════════════════"
        echo "WebSocket Streaming Test"
        echo "═══════════════════════════════════════════════════════════════════════════"
        echo ""
        cd "$HUMMINGBOT_ROOT"
        python scripts/test_extended_websocket.py
        ;;
    4)
        echo ""
        echo "═══════════════════════════════════════════════════════════════════════════"
        echo "HTTP Streaming Test"
        echo "═══════════════════════════════════════════════════════════════════════════"
        echo ""
        cd "$HUMMINGBOT_ROOT"
        python scripts/test_extended_http_stream.py
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Tests completed!"
echo ""
echo "📊 Next Steps:"
echo "   1. Review test output above"
echo "   2. Compare message counts (balance updates especially)"
echo "   3. Check saved JSON files if you opted to save"
echo "   4. Read EXTENDED_STREAMING_TESTS.md for analysis guide"
echo ""
