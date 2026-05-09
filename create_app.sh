#!/bin/bash
set -e

APP_NAME="Typeless"
APP_PATH="$HOME/Desktop/$APP_NAME.app"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$(which python3)"

echo "=== 建立 $APP_NAME.app ==="

# Create bundle structure
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# Main executable (shell script that launches python3)
cat > "$APP_PATH/Contents/MacOS/$APP_NAME" << EOF
#!/bin/bash
# Load API key from dedicated env file (reliable regardless of launch method)
if [ -f "\$HOME/.typeless_env" ]; then
    export \$(grep -v '^#' "\$HOME/.typeless_env" | xargs)
fi
exec "$PYTHON" "$SCRIPT_DIR/main.py"
EOF
chmod +x "$APP_PATH/Contents/MacOS/$APP_NAME"

# Info.plist — LSUIElement=true means no Dock icon, menu bar only
cat > "$APP_PATH/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.typeless.app</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSMicrophoneUsageDescription</key>
    <string>Typeless needs microphone access for voice input.</string>
</dict>
</plist>
EOF

echo "✅ Typeless.app 建立完成：$APP_PATH"
echo ""

# Add to Login Items (auto-start on login)
osascript << APPLESCRIPT
tell application "System Events"
    set existingItems to name of every login item
    if "$APP_NAME" is not in existingItems then
        make login item at end with properties {path:"$APP_PATH", hidden:false}
        return "✅ 已加入開機自動啟動"
    else
        return "ℹ️  開機自動啟動已設定"
    end if
end tell
APPLESCRIPT

echo ""
echo "=== 下一步（只需做一次）==="
echo "1. 雙擊桌面的 Typeless.app 啟動"
echo "2. 系統設定 > 隱私與安全性 > 輔助使用"
echo "   把「Typeless」加入清單並打開"
echo "3. 重新雙擊 Typeless.app"
echo "4. 之後每次開機會自動啟動"
