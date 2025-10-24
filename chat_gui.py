"""
FakeMan 图形聊天界面
使用Tkinter创建简洁的聊天窗口
"""

import tkinter as tk
from tkinter import scrolledtext, ttk
import json
import time
from pathlib import Path
from datetime import datetime
import threading


class ChatGUI:
    """聊天图形界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FakeMan 聊天界面")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # 通信文件路径
        self.comm_dir = Path("data/communication")
        self.input_file = self.comm_dir / "user_input.json"
        self.output_file = self.comm_dir / "ai_output.json"
        
        # 最后读取的时间戳
        self.last_ai_timestamp = 0
        
        # 创建界面
        self._create_widgets()
        
        # 启动AI输出监听线程
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_ai_output, daemon=True)
        self.monitor_thread.start()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部标题
        title_frame = tk.Frame(main_frame, bg='#2c3e50', height=60)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🤖 FakeMan 聊天",
            font=('Microsoft YaHei UI', 18, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=15)
        
        # 聊天区域容器
        chat_container = tk.Frame(main_frame, bg='#f0f0f0')
        chat_container.pack(fill=tk.BOTH, expand=True)
        
        # 左侧 - AI输出区域
        left_frame = tk.Frame(chat_container, bg='#f0f0f0')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        left_label = tk.Label(
            left_frame,
            text="💬 AI 输出",
            font=('Microsoft YaHei UI', 12, 'bold'),
            bg='#f0f0f0',
            fg='#34495e'
        )
        left_label.pack(anchor=tk.W, pady=(0, 5))
        
        # AI输出文本框
        self.ai_text = scrolledtext.ScrolledText(
            left_frame,
            wrap=tk.WORD,
            font=('Microsoft YaHei UI', 10),
            bg='#ecf0f1',
            fg='#2c3e50',
            relief=tk.FLAT,
            padx=10,
            pady=10,
            state=tk.DISABLED
        )
        self.ai_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置AI文本标签
        self.ai_text.tag_config('timestamp', foreground='#7f8c8d', font=('Microsoft YaHei UI', 8))
        self.ai_text.tag_config('ai_message', foreground='#2980b9', font=('Microsoft YaHei UI', 10))
        self.ai_text.tag_config('system', foreground='#27ae60', font=('Microsoft YaHei UI', 9, 'italic'))
        
        # 右侧 - 用户输入区域
        right_frame = tk.Frame(chat_container, bg='#f0f0f0')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        right_label = tk.Label(
            right_frame,
            text="✍️ 我的输入",
            font=('Microsoft YaHei UI', 12, 'bold'),
            bg='#f0f0f0',
            fg='#34495e'
        )
        right_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 用户历史记录
        self.user_text = scrolledtext.ScrolledText(
            right_frame,
            wrap=tk.WORD,
            font=('Microsoft YaHei UI', 10),
            bg='#fef9e7',
            fg='#2c3e50',
            relief=tk.FLAT,
            padx=10,
            pady=10,
            state=tk.DISABLED,
            height=15
        )
        self.user_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 配置用户文本标签
        self.user_text.tag_config('timestamp', foreground='#7f8c8d', font=('Microsoft YaHei UI', 8))
        self.user_text.tag_config('user_message', foreground='#8e44ad', font=('Microsoft YaHei UI', 10))
        
        # 输入框标签
        input_label = tk.Label(
            right_frame,
            text="💭 输入消息：",
            font=('Microsoft YaHei UI', 10),
            bg='#f0f0f0',
            fg='#34495e'
        )
        input_label.pack(anchor=tk.W, pady=(5, 5))
        
        # 输入框
        input_frame = tk.Frame(right_frame, bg='#f0f0f0')
        input_frame.pack(fill=tk.X)
        
        self.input_text = tk.Text(
            input_frame,
            wrap=tk.WORD,
            font=('Microsoft YaHei UI', 10),
            bg='white',
            fg='#2c3e50',
            relief=tk.SOLID,
            borderwidth=1,
            padx=10,
            pady=10,
            height=5
        )
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 绑定快捷键
        self.input_text.bind('<Control-Return>', lambda e: self.send_message())
        
        # 发送按钮
        self.send_button = tk.Button(
            input_frame,
            text="发送\n(Ctrl+Enter)",
            font=('Microsoft YaHei UI', 10, 'bold'),
            bg='#3498db',
            fg='white',
            activebackground='#2980b9',
            activeforeground='white',
            relief=tk.FLAT,
            cursor='hand2',
            width=10,
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 底部状态栏
        status_frame = tk.Frame(main_frame, bg='#ecf0f1', height=30)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="🟢 已连接 | 等待消息...",
            font=('Microsoft YaHei UI', 9),
            bg='#ecf0f1',
            fg='#27ae60'
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
    
    def _format_timestamp(self, timestamp=None):
        """格式化时间戳"""
        if timestamp is None:
            timestamp = time.time()
        return datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
    
    def _append_to_text(self, text_widget, message, tag=None, timestamp=None):
        """向文本框追加内容"""
        text_widget.config(state=tk.NORMAL)
        
        # 添加时间戳
        time_str = self._format_timestamp(timestamp)
        text_widget.insert(tk.END, f"[{time_str}] ", 'timestamp')
        
        # 添加消息
        if tag:
            text_widget.insert(tk.END, message + "\n\n", tag)
        else:
            text_widget.insert(tk.END, message + "\n\n")
        
        text_widget.see(tk.END)
        text_widget.config(state=tk.DISABLED)
    
    def send_message(self):
        """发送用户消息"""
        message = self.input_text.get("1.0", tk.END).strip()
        
        if not message:
            return
        
        # 显示在用户历史区域
        self._append_to_text(
            self.user_text,
            f"我: {message}",
            'user_message'
        )
        
        # 写入通信文件
        try:
            data = {
                'text': message,
                'timestamp': time.time(),
                'metadata': {}
            }
            
            with open(self.input_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 更新状态
            self.status_label.config(
                text="🟡 已发送 | 等待AI回复...",
                fg='#f39c12'
            )
            
            # 清空输入框
            self.input_text.delete("1.0", tk.END)
            
        except Exception as e:
            self._append_to_text(
                self.ai_text,
                f"❌ 发送失败: {str(e)}",
                'system'
            )
    
    def _monitor_ai_output(self):
        """监听AI输出（后台线程）"""
        while self.running:
            try:
                if self.output_file.exists():
                    with open(self.output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 检查是否有新消息
                    if data and data.get('text'):
                        timestamp = data.get('timestamp', 0)
                        
                        if timestamp > self.last_ai_timestamp:
                            self.last_ai_timestamp = timestamp
                            
                            # 获取消息内容
                            text = data['text']
                            action_type = data.get('action_type', 'response')
                            thought_summary = data.get('thought_summary', '')
                            
                            # 格式化消息
                            if action_type == 'proactive':
                                prefix = "🤖 AI (主动): "
                            else:
                                prefix = "🤖 AI: "
                            
                            message = f"{prefix}{text}"
                            
                            # 如果有思考摘要，添加到消息中
                            if thought_summary:
                                message += f"\n💭 思考: {thought_summary}"
                            
                            # 显示AI消息
                            self.root.after(0, self._append_to_text,
                                          self.ai_text, message, 'ai_message', timestamp)
                            
                            # 更新状态
                            self.root.after(0, self.status_label.config,
                                          {'text': '🟢 已连接 | AI已回复',
                                           'fg': '#27ae60'})
                
            except Exception as e:
                # 忽略读取错误，继续监听
                pass
            
            time.sleep(0.5)  # 每0.5秒检查一次
    
    def run(self):
        """运行GUI"""
        # 添加关闭处理
        def on_closing():
            self.running = False
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # 显示欢迎消息
        welcome = """欢迎使用 FakeMan 聊天界面！

🎯 使用说明：
  • 在右侧输入框输入消息
  • 点击"发送"或按 Ctrl+Enter 发送
  • AI的回复会显示在左侧
  • 你的消息历史在右上方

💡 提示：
  • 确保 main.py 正在运行
  • 支持主动对话和响应对话
  • 所有消息都带时间戳

开始聊天吧！👋"""
        
        self._append_to_text(
            self.ai_text,
            welcome,
            'system'
        )
        
        self.root.mainloop()


if __name__ == '__main__':
    # 确保通信目录存在
    Path("data/communication").mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("FakeMan 图形聊天界面")
    print("="*60)
    print("\n启动GUI...")
    print("请确保 main.py 正在运行以接收消息")
    print("\n关闭窗口可退出程序\n")
    
    app = ChatGUI()
    app.run()

