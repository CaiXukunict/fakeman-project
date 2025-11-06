"""
FakeMan 图形聊天界面（重构版）
单一对话框显示所有消息，按时间顺序排列
"""

import tkinter as tk
from tkinter import scrolledtext
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
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # 通信文件路径
        self.comm_dir = Path("data/communication")
        self.input_file = self.comm_dir / "user_input.json"
        self.output_file = self.comm_dir / "ai_output.json"
        
        # 聊天历史文件
        self.history_file = self.comm_dir / "chat_history.json"
        
        # 聊天历史
        self.chat_history = []
        
        # 最后读取的时间戳
        self.last_ai_timestamp = 0
        
        # 加载历史记录
        self._load_history()
        
        # 创建界面
        self._create_widgets()
        
        # 显示历史记录
        self._display_history()
        
        # 启动AI输出监听线程
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_ai_output, daemon=True)
        self.monitor_thread.start()
    
    def _load_history(self):
        """加载聊天历史"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.chat_history = data.get('messages', [])
                    # 更新最后时间戳
                    if self.chat_history:
                        self.last_ai_timestamp = max(
                            msg.get('timestamp', 0) 
                            for msg in self.chat_history 
                            if msg['type'] == 'ai'
                        ) if any(msg['type'] == 'ai' for msg in self.chat_history) else 0
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            self.chat_history = []
    
    def _save_history(self):
        """保存聊天历史"""
        try:
            self.comm_dir.mkdir(parents=True, exist_ok=True)
            data = {
                'messages': self.chat_history,
                'last_updated': time.time()
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
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
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # 清空历史按钮
        clear_button = tk.Button(
            title_frame,
            text="🗑️ 清空历史",
            font=('Microsoft YaHei UI', 10),
            bg='#e74c3c',
            fg='white',
            activebackground='#c0392b',
            activeforeground='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._clear_history
        )
        clear_button.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # 对话显示区域
        chat_label = tk.Label(
            main_frame,
            text="💬 对话记录",
            font=('Microsoft YaHei UI', 12, 'bold'),
            bg='#f0f0f0',
            fg='#34495e'
        )
        chat_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 对话文本框
        self.chat_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            font=('Microsoft YaHei UI', 10),
            bg='white',
            fg='#2c3e50',
            relief=tk.FLAT,
            padx=15,
            pady=15
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.chat_text.config(state=tk.DISABLED)
        
        # 配置文本标签
        self.chat_text.tag_config('timestamp', foreground='#95a5a6', font=('Microsoft YaHei UI', 8))
        self.chat_text.tag_config('user_name', foreground='#8e44ad', font=('Microsoft YaHei UI', 10, 'bold'))
        self.chat_text.tag_config('user_message', foreground='#34495e', font=('Microsoft YaHei UI', 10))
        self.chat_text.tag_config('ai_name', foreground='#2980b9', font=('Microsoft YaHei UI', 10, 'bold'))
        self.chat_text.tag_config('ai_message', foreground='#34495e', font=('Microsoft YaHei UI', 10))
        self.chat_text.tag_config('system', foreground='#27ae60', font=('Microsoft YaHei UI', 9, 'italic'))
        self.chat_text.tag_config('thought', foreground='#7f8c8d', font=('Microsoft YaHei UI', 9, 'italic'))
        self.chat_text.tag_config('separator', foreground='#ecf0f1')
        
        # 输入区域标签
        input_label = tk.Label(
            main_frame,
            text="✍️ 输入消息：",
            font=('Microsoft YaHei UI', 10),
            bg='#f0f0f0',
            fg='#34495e'
        )
        input_label.pack(anchor=tk.W, pady=(5, 5))
        
        # 输入框容器
        input_frame = tk.Frame(main_frame, bg='#f0f0f0')
        input_frame.pack(fill=tk.X)
        
        # 输入文本框
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
            height=4
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
        
        # 消息计数
        self.count_label = tk.Label(
            status_frame,
            text=f"📊 消息: {len(self.chat_history)}",
            font=('Microsoft YaHei UI', 9),
            bg='#ecf0f1',
            fg='#7f8c8d'
        )
        self.count_label.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def _format_timestamp(self, timestamp=None):
        """格式化时间戳"""
        if timestamp is None:
            timestamp = time.time()
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    def _display_history(self):
        """显示历史记录"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete('1.0', tk.END)
        
        if not self.chat_history:
            welcome = """欢迎使用 FakeMan 聊天界面！

🎯 使用说明：
  • 在下方输入框输入消息
  • 点击"发送"或按 Ctrl+Enter 发送
  • 所有对话记录显示在此处

💡 提示：
  • 确保 main.py 正在运行
  • 所有消息自动保存
  • 可以点击"清空历史"清除记录

开始聊天吧！👋
"""
            self.chat_text.insert(tk.END, welcome, 'system')
        else:
            for msg in self.chat_history:
                self._append_message_to_display(msg)
        
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)
    
    def _append_message_to_display(self, msg):
        """将消息添加到显示区域"""
        msg_type = msg['type']
        content = msg['content']
        timestamp = msg.get('timestamp', time.time())
        
        # 时间戳
        time_str = self._format_timestamp(timestamp)
        self.chat_text.insert(tk.END, f"[{time_str}]\n", 'timestamp')
        
        if msg_type == 'user':
            # 用户消息
            self.chat_text.insert(tk.END, "👤 你: ", 'user_name')
            self.chat_text.insert(tk.END, f"{content}\n", 'user_message')
        
        elif msg_type == 'ai':
            # AI消息
            action_type = msg.get('action_type', 'response')
            if action_type == 'proactive':
                self.chat_text.insert(tk.END, "🤖 AI (主动): ", 'ai_name')
            else:
                self.chat_text.insert(tk.END, "🤖 AI: ", 'ai_name')
            
            self.chat_text.insert(tk.END, f"{content}\n", 'ai_message')
            
            # 思考摘要
            thought = msg.get('thought_summary', '')
            if thought:
                self.chat_text.insert(tk.END, f"   💭 思考: {thought}\n", 'thought')
        
        elif msg_type == 'system':
            # 系统消息
            self.chat_text.insert(tk.END, f"ℹ️ {content}\n", 'system')
        
        # 分隔线
        self.chat_text.insert(tk.END, "─" * 50 + "\n\n", 'separator')
    
    def _add_message(self, msg_type, content, **kwargs):
        """添加消息到历史"""
        message = {
            'type': msg_type,
            'content': content,
            'timestamp': time.time(),
            **kwargs
        }
        
        self.chat_history.append(message)
        
        # 更新显示
        self.chat_text.config(state=tk.NORMAL)
        self._append_message_to_display(message)
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
        
        # 更新计数
        self.count_label.config(text=f"📊 消息: {len(self.chat_history)}")
        
        # 保存历史
        self._save_history()
    
    def send_message(self):
        """发送用户消息"""
        message = self.input_text.get("1.0", tk.END).strip()
        
        if not message:
            return
        
        # 添加到历史
        self._add_message('user', message)
        
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
            self._add_message('system', f"❌ 发送失败: {str(e)}")
    
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
                            
                            # 添加到历史
                            self.root.after(0, self._add_message, 'ai', text,
                                          action_type=action_type,
                                          thought_summary=thought_summary)
                            
                            # 更新状态
                            self.root.after(0, self.status_label.config,
                                          {'text': '🟢 已连接 | AI已回复',
                                           'fg': '#27ae60'})
                
            except Exception as e:
                # 忽略读取错误，继续监听
                pass
            
            time.sleep(0.5)  # 每0.5秒检查一次
    
    def _clear_history(self):
        """清空聊天历史"""
        # 确认对话框
        confirm = tk.Toplevel(self.root)
        confirm.title("确认")
        confirm.geometry("300x120")
        confirm.configure(bg='#f0f0f0')
        confirm.resizable(False, False)
        
        # 居中显示
        confirm.transient(self.root)
        confirm.grab_set()
        
        label = tk.Label(
            confirm,
            text="确定要清空所有聊天记录吗？\n此操作不可恢复！",
            font=('Microsoft YaHei UI', 10),
            bg='#f0f0f0',
            fg='#e74c3c'
        )
        label.pack(pady=20)
        
        button_frame = tk.Frame(confirm, bg='#f0f0f0')
        button_frame.pack(pady=10)
        
        def do_clear():
            self.chat_history = []
            self.last_ai_timestamp = 0
            self._save_history()
            self._display_history()
            self.count_label.config(text=f"📊 消息: 0")
            confirm.destroy()
        
        tk.Button(
            button_frame,
            text="确定",
            font=('Microsoft YaHei UI', 9),
            bg='#e74c3c',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            width=8,
            command=do_clear
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="取消",
            font=('Microsoft YaHei UI', 9),
            bg='#95a5a6',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            width=8,
            command=confirm.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def run(self):
        """运行GUI"""
        # 添加关闭处理
        def on_closing():
            self.running = False
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
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
