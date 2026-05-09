#!/bin/bash
while IFS='=' read -r key value; do
    [[ "$key" =~ ^[[:space:]]*# ]] && continue
    [[ -z "$key" ]] && continue
    export "$key=$value"
done < "$HOME/.typeless_env"
exec /opt/anaconda3/bin/python3 /Users/yao/Desktop/CLAUDE/Typeless/main.py
