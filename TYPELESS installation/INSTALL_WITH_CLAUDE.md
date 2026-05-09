# Typeless 一鍵安裝指南（給 Claude Code 用）

> **使用方式**：把這份檔案丟給 Claude Code，跟它說「請依照這份文件安裝 Typeless」，它會一步步執行並驗證。

---

## 給 Claude 的指令（⚠️ 請完整遵守）

你正在幫使用者安裝 **Typeless**，一個 macOS 上的語音輸入工具。請依照下面 8 個步驟順序執行，**每一步完成後都要驗證再進下一步**。如果遇到錯誤，先讀「常見問題」再決定怎麼處理。**不要跳步**。

需要使用者輸入的東西只有一項：**Groq API Key**。請在步驟 4 主動問。

---

## 系統需求（先檢查）

執行以下指令確認環境：

```bash
sw_vers -productVersion         # 應為 macOS 13+ (本專案測過 26.4.1)
which python3                   # 應該指到 /opt/anaconda3/bin/python3
ls /opt/anaconda3/python.app    # 應該存在
```

如果使用者沒有 Anaconda Python，請先請他到 [anaconda.com](https://www.anaconda.com/download) 下載安裝後再繼續。

---

## 步驟 1：取得程式碼

```bash
mkdir -p ~/Desktop/CLAUDE
git clone https://github.com/chingyaosu/Typeless.git ~/Desktop/CLAUDE/Typeless
cd ~/Desktop/CLAUDE/Typeless
```

驗證：`ls ~/Desktop/CLAUDE/Typeless/main.py` 應該存在。

---

## 步驟 2：安裝 Python 套件

```bash
pip install -r ~/Desktop/CLAUDE/Typeless/requirements.txt
```

如果有 Anaconda 過時的 `pathlib` 套件衝突（會在後面導致 `ImportError: cannot import name 'Sequence' from 'collections'`），先移除：

```bash
pip uninstall -y pathlib
```

驗證：

```bash
python3 -c "import groq, sounddevice, rumps, Quartz, AVFoundation; print('✅ 全部 OK')"
```

如果 AVFoundation 缺：`pip install pyobjc-framework-AVFoundation`

---

## 步驟 3：清理舊 pyc 快取

```bash
find ~/Desktop/CLAUDE/Typeless -name "*.pyc" -delete
find ~/Desktop/CLAUDE/Typeless -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
```

---

## 步驟 4：取得 Groq API Key

**請主動問使用者**：

> 「請去 [console.groq.com](https://console.groq.com) 註冊（可用 Google 登入），到 API Keys 頁面建一個新 key（gsk_ 開頭），然後貼給我。」

拿到後，**用使用者實際的 key 取代下面的 YOUR_KEY**：

```bash
echo "GROQ_API_KEY=YOUR_KEY" > ~/.typeless_env
chmod 600 ~/.typeless_env
```

驗證 key 有效：

```bash
export GROQ_API_KEY=$(cat ~/.typeless_env | cut -d= -f2)
python3 -c "
from groq import Groq
import os
client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
print('✅ API Key 有效，可用模型數:', len(client.models.list().data))
"
```

如果失敗，請使用者重新確認 key。

---

## 步驟 5：建立 Typeless.app（解決 macOS 權限）

直接執行 python3 main.py 會被 macOS 擋（Gatekeeper、TCC 都認 .app bundle）。複製 python.app 改 Info.plist：

```bash
# 移除舊的（如果有）
rm -rf /Applications/Typeless.app 2>/dev/null

# 複製 anaconda 的 python.app 當基底
cp -R /opt/anaconda3/python.app /Applications/Typeless.app

# 寫入正確的 Info.plist
cat > /Applications/Typeless.app/Contents/Info.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>python</string>
    <key>CFBundleIdentifier</key>
    <string>com.typeless.app</string>
    <key>CFBundleName</key>
    <string>Typeless</string>
    <key>CFBundleDisplayName</key>
    <string>Typeless</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSMicrophoneUsageDescription</key>
    <string>Typeless 需要麥克風來接收你的語音輸入</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>Typeless 需要傳送鍵盤事件來貼上文字</string>
</dict>
</plist>
EOF

# 重新簽名（ad-hoc）
codesign --force --deep --sign - /Applications/Typeless.app
```

驗證：

```bash
ls /Applications/Typeless.app/Contents/MacOS/python
plutil -p /Applications/Typeless.app/Contents/Info.plist | grep Microphone
```

---

## 步驟 6：建立 LaunchAgent（開機自動啟動）

⚠️ 必須用使用者的實際家目錄路徑（不要用 `~` 或 `$HOME`）。先抓一下：

```bash
USER_HOME=$HOME
echo "User home: $USER_HOME"
```

然後建立 plist（用實際路徑替換）：

```bash
cat > ~/Library/LaunchAgents/com.typeless.app.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.typeless.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/Typeless.app/Contents/MacOS/python</string>
        <string>$USER_HOME/Desktop/CLAUDE/Typeless/main.py</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONHOME</key>
        <string>/opt/anaconda3</string>
        <key>PYTHONPATH</key>
        <string>/opt/anaconda3/lib/python3.11/site-packages</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/typeless.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/typeless.log</string>
</dict>
</plist>
EOF

launchctl unload ~/Library/LaunchAgents/com.typeless.app.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.typeless.app.plist
sleep 4
```

驗證：

```bash
launchctl list | grep typeless    # 第二欄應為 0
cat /tmp/typeless.log             # 應該有 "Microphone status: 3" 等訊息
```

如果第二欄不是 0，看 log 找原因（看「常見問題」）。

---

## 步驟 7：請使用者授權 macOS 權限

⚠️ **這步必須使用者親自做，Claude 無法代勞。**

請告訴使用者：

> **A. 輔助使用（鍵盤監聽）**
> 1. 系統設定 > 隱私與安全性 > **輔助使用**
> 2. 從 Finder 拖 `/Applications/Typeless.app` 進清單（或按 + 加入）
> 3. **打開開關**
>
> **B. 麥克風**
> 1. 等一下按 Option+Space 時，macOS 會自動跳出對話框 → 點「允許」

完成後，請使用者按 Option+Space 一次（不用講話），然後執行：

```bash
launchctl unload ~/Library/LaunchAgents/com.typeless.app.plist
launchctl load ~/Library/LaunchAgents/com.typeless.app.plist
sleep 3
cat /tmp/typeless.log
```

**最終檢查表：**

```
[Typeless] Microphone status: 3 (3 = authorized)        ← 必須是 3
[Typeless] Process: /Applications/Typeless.app/...
[Typeless] Accessibility: ✅ AUTHORIZED                  ← 必須是 ✅
```

兩個都通過才算安裝成功。

---

## 步驟 8：實測

請使用者：
1. 點任何文字輸入框（這個對話框、Notes、Slack 都行）
2. 按住 Option+Space → 聽到 Tink 聲 → 圖示變 🔴 → **螢幕上方出現浮動視窗「🔴 Recording…」**
3. 說一句話：「測試一下這個 voice input 中英混合的辨識」
4. 放開 → 聽到 Pop 聲 → **浮動視窗變「⏳ Analyzing…」**
5. 1~2 秒後文字自動貼入 → **浮動視窗顯示貼上的文字（綠色，2.5 秒後消失）**

如果文字成功貼入 → ✅ 安裝完成！

### 關於浮動狀態視窗

從 v1.1 開始，Typeless 內建螢幕上方的浮動狀態視窗（`status_window.py`），會顯示：
- 🔴 Recording… — 錄音中
- ⏳ Analyzing… — 上傳轉錄與 AI 潤飾中
- 〈結果文字〉— 完成後綠字顯示 2.5 秒
- ⌘ 〈指令名〉— 觸發語音指令（如 send / undo）時顯示

視窗特性：
- 永遠浮在所有視窗之上
- 點擊穿透（不會擋住操作）
- 不搶焦點

實作細節（給除錯用）：用 PyObjC 的 `NSPanel` + `setIgnoresMouseEvents_(True)` + `NSFloatingWindowLevel`。所有 UI 更新透過 `performSelectorOnMainThread_` 從背景 thread 安全派送到主執行緒（AppKit 強制要求）。

如果浮動視窗沒出現，常見原因：
- `pyobjc-framework-Cocoa` 版本太舊（需要 ≥ 10.0）
- 看 `/tmp/typeless.log` 是否有 `NSPanel` 相關錯誤

---

## 常見問題

### `[Typeless] Accessibility: ❌ NOT AUTHORIZED`
- 使用者沒授權，或加錯路徑
- 確認加入清單的是 `/Applications/Typeless.app`，不是其他
- **重點**：移動 .app 後 TCC 會失效，要重新加

### Whisper 一直辨識成 "THANK YOU"
- 麥克風授權問題，Whisper 收到沉默音訊
- 確認步驟 5 的 Info.plist 有 `NSMicrophoneUsageDescription`
- 確認步驟 7B 的對話框有點允許

### 按 Option+Space 只插入空白字元
- CGEventTap 被 macOS 暫時停用
- 重啟：`launchctl kickstart -k gui/$UID/com.typeless.app`

### `ImportError: cannot import name 'Sequence' from 'collections'`
- Anaconda 過時 pathlib 套件
- 解：`pip uninstall -y pathlib`

### Tink 開始音延遲到放開後才響
- 確認用的是 main.py 最新版（recorder.py 應該是「永遠開著 stream」的版本）
- 看 `recorder.py` 的 `_stream.start()` 應該在 `__init__` 裡，不是在 `start()` 裡

### LaunchAgent 一直顯示 exit code 不是 0
```bash
cat /tmp/typeless.log              # 看實際錯誤
launchctl list | grep typeless     # 看 exit code
```
常見：
- `-6`：SIGABRT，通常是 import 錯誤
- `78`：configuration error，plist 格式錯
- `1`：Python 程式錯誤，看 log

---

## 安裝後管理指令

```bash
# 停止
launchctl unload ~/Library/LaunchAgents/com.typeless.app.plist

# 啟動
launchctl load ~/Library/LaunchAgents/com.typeless.app.plist

# 重啟
launchctl kickstart -k gui/$UID/com.typeless.app

# 看 log
tail -f /tmp/typeless.log

# 完全移除
launchctl unload ~/Library/LaunchAgents/com.typeless.app.plist
rm ~/Library/LaunchAgents/com.typeless.app.plist
rm -rf /Applications/Typeless.app
rm ~/.typeless_env
rm -rf ~/Desktop/CLAUDE/Typeless
# 還要去系統設定移除 Accessibility 和麥克風的 Typeless 項目
```

---

## 使用方式速查

| 操作 | 動作 |
|------|------|
| 按住 Option+Space | 開始錄音 |
| 放開 | 結束 → AI 潤飾 → 自動貼入 |
| 說「**全中文** ...」 | 強制輸出繁體中文 |
| 說「**全英文** ...」 | 強制輸出英文 |
| 說「**重新說**」/「**重來**」 | Cmd+Z 復原上次貼上 |
| 說「**全選**」 | Cmd+A |
| 說「**換行**」 | Enter |
| 說「**複製**」/「**剪下**」 | Cmd+C / Cmd+X |

App 會自動偵測當前 App 調整潤飾語氣（Slack 輕鬆 / Mail 正式 / VS Code 技術）。

## 視覺回饋

| 位置 | 狀態 |
|------|------|
| Menu bar 圖示 | ⌨️ 待機 / 🔴 錄音中 / ⏳ 處理中 |
| 螢幕上方浮動視窗 | 🔴 Recording / ⏳ Analyzing / 〈結果文字〉 |
| 系統音效 | Tink 開始 / Pop 結束 / Morse 觸發指令 |
