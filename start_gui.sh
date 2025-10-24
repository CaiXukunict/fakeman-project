#!/bin/bash

echo "================================================"
echo "   FakeMan 图形聊天界面"
echo "================================================"
echo ""
echo "正在启动..."
echo ""
echo "💡 提示：请确保 main.py 已在另一个终端运行"
echo ""

python3 chat_gui.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 启动失败！"
    echo "请检查："
    echo "  1. Python3 是否已安装"
    echo "  2. 依赖是否已安装 (pip3 install -r requirements.txt)"
    echo ""
    read -p "按回车键退出..."
fi

