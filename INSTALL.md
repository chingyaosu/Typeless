# Typeless 安裝指南

macOS 上的語音輸入工具：按住 `Option+Space` → 說話 → 放開 → AI 潤飾後的文字自動貼入當前視窗。

支援中英混合、Slack/Mail/VS Code 等 App 自動調整語氣、語音指令（重新說、全選等）。

---

## 系統需求

- macOS（測試於 macOS 26 / Sequoia 26.4.1）
- Anaconda Python 3.11
- Groq API Key（免費，[console.groq.com](https://console.groq.com)）

---

## 安裝步驟

### 1. 取得程式碼

```bash
git clone https://github.com/chingyaosu/Typeless.git ~/Desktop/CLAUDE/Typeless
cd ~/Desktop/CLAUDE/Typeless
```

### 2. 安裝相依套件

```bash
pip install -r requirements.txt
```

如果 Anaconda 有舊的 `pathlib` 套件衝突（Python 3.11+ 不需要），先移除：

```bash
pip uninstall -y pathlib
```

### 3. 設定 Groq API Key

```bash
echo "GROQ_API_KEY=你的_groq_api_key" > ~/.typeless_env
chmod 600 ~/.typeless_env
```

### 4. 建立 Typeless.app（解決 macOS 權限）

直接用 Anaconda 的 `python3` 跑會被 macOS Gatekeeper 擋住，且沒有麥克風授權描述。
所以要做一個正規的 .app bundle：

```bash
# 複製 python.app 當基底
cp -R /opt/anaconda3/python.app /Applications/Typeless.app

# 寫入正確的 Info.plist（含 microphone usage 描述、自訂 bundle ID）
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

# 重新簽名
codesign --force --deep --sign - /Applications/Typeless.app
```

### 5. 建立 LaunchAgent（開機自動啟動）

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
        <string>$HOME/Desktop/CLAUDE/Typeless/main.py</string>
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

launchctl load ~/Library/LaunchAgents/com.typeless.app.plist
```

### 6. 授權 macOS 權限（首次只需一次）

#### 6a. 輔助使用（鍵盤監聽）

1. 系統設定 > 隱私與安全性 > **輔助使用**
2. 從 Finder 拖 `/Applications/Typeless.app` 進清單
3. 開關打開

#### 6b. 麥克風

按一次 Option+Space，macOS 會自動跳出麥克風授權對話框 → 點允許。

驗證權限狀態：

```bash
cat /tmp/typeless.log
# 應該看到：
# [Typeless] Microphone status: 3 (3 = authorized)
# [Typeless] Accessibility: ✅ AUTHORIZED
```

---

## 使用方式

| 操作 | 動作 |
|------|------|
| 按住 Option+Space | 開始錄音（Tink 聲）|
| 說話 | … |
| 放開 | 結束（Pop 聲）→ AI 潤飾 → 自動貼入 |

### 語音指令（說完就執行，不貼文字）

| 說 | 動作 |
|----|------|
| 重新說 / 重來 / 刪掉 | Cmd+Z 復原 |
| 全選 | Cmd+A |
| 換行 | Enter |
| 複製 / 剪下 | Cmd+C / Cmd+X |

### 強制翻譯

- 「**全中文** 然後說的內容」→ 全部轉繁體中文
- 「**全英文** then content」→ 全部轉英文

### App 自動語氣

| 當前 App | 語氣 |
|----------|------|
| Slack / LINE / Messages | 輕鬆口語 |
| Mail / Outlook | 正式專業 |
| Notion / Obsidian | 清楚結構化 |
| VS Code / Terminal | 技術用語不動 |

---

## 常見問題

### 按 Option+Space 只插入空白

CGEventTap 被 macOS 暫時停用了。重啟 app：
```bash
launchctl kickstart -k gui/$UID/com.typeless.app
```

### 文字一直是 "THANK YOU"

麥克風沒授權，Whisper 收到無聲音訊。重做步驟 6b。

### 沒聽到 Tink 聲

檢查 LaunchAgent 是否在跑：
```bash
launchctl list | grep typeless
# status 應該是 0
```

### 修改設定後重啟 app

```bash
launchctl unload ~/Library/LaunchAgents/com.typeless.app.plist
launchctl load ~/Library/LaunchAgents/com.typeless.app.plist
```

---

## 架構

| 檔案 | 角色 |
|------|------|
| `main.py` | 主程式，rumps menu bar app |
| `hotkey.py` | CGEventTap 全域熱鍵（攔截 Option+Space） |
| `recorder.py` | sounddevice 錄音（永遠開著 stream，避免 audio session 衝突）|
| `api.py` | Groq Whisper 轉錄 + LLaMA 潤飾 |
| `output.py` | pbcopy + Cmd+V 貼入文字 |

### 為什麼這樣設計？

1. **CGEventTap 而非 pynput** — 才能攔截 Space 不讓它漏到當前視窗
2. **永遠開著的 audio stream** — 避免按下去的瞬間 sounddevice 搶 audio session 把 Tink 聲擠掉
3. **AudioServicesPlaySystemSound + afplay 雙保險** — 不同情境下至少一個會響
4. **app bundle 而非裸 python3** — macOS 26 的 TCC 需要 bundle ID 才能授權
5. **LaunchAgent 而非 .app 雙擊** — Gatekeeper 對 ad-hoc 簽名 .app 限制太多
