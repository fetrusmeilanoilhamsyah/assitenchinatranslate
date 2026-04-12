#!/bin/bash

# Quick Start Script untuk Translator Bot
# Author: @FEE999888

set -e

echo "🚀 Translator Bot - Quick Start"
echo "================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "❌ Jangan run sebagai root!"
   exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 tidak ditemukan! Install dulu:"
    echo "   sudo apt update && sudo apt install python3 python3-pip python3-venv -y"
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q

# Check .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file tidak ditemukan!"
    echo "📝 Copying .env.example to .env..."
    cp .env.example .env
    echo ""
    echo "⚠️  PENTING: Edit .env dan masukkan BOT_TOKEN!"
    echo "   nano .env"
    echo ""
    read -p "Press Enter setelah edit .env..."
fi

# Validate .env
if grep -q "YOUR_BOT_TOKEN_HERE" .env; then
    echo "❌ BOT_TOKEN masih default!"
    echo "   Edit .env dan ganti dengan token asli dari @BotFather"
    echo "   nano .env"
    exit 1
fi

echo "✅ Configuration OK"

# Create directories
mkdir -p logs data

echo ""
echo "✅ Setup selesai!"
echo ""
echo "📝 Cara menjalankan:"
echo "   1. Development: python bot.py"
echo "   2. Background: nohup python bot.py > /dev/null 2>&1 &"
echo "   3. Systemd: sudo cp translator-bot.service /etc/systemd/system/"
echo ""
echo "🔍 Monitor logs:"
echo "   tail -f logs/bot.log"
echo ""

read -p "Mau langsung run bot sekarang? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting bot..."
    python bot.py
fi
