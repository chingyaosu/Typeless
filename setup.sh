#!/bin/bash
set -e

echo "=== Typeless Setup ==="

# Install dependencies
pip install -r requirements.txt

# Ask for API key if not set
if [ -z "$GROQ_API_KEY" ]; then
    echo ""
    echo "請輸入你的 Groq API Key（從 console.groq.com 取得）："
    read -r key
    echo "export GROQ_API_KEY=$key" >> ~/.zshrc
    export GROQ_API_KEY=$key
    echo "✅ API Key 已儲存到 ~/.zshrc"
fi

echo ""
echo "⚠️  首次使用前，請至："
echo "   系統設定 > 隱私與安全性 > 輔助使用"
echo "   將 Terminal（或你的終端機 App）加入允許清單"
echo ""
echo "啟動方式："
echo "   python3 main.py"
echo ""
echo "使用方式："
echo "   按住 Option+Space 說話，放開後文字自動貼入"
echo "   說「全中文」開頭 → 強制輸出繁體中文"
echo "   說「全英文」開頭 → 強制輸出英文"
