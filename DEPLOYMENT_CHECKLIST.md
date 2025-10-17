# FakeMan 持续思考系统 - 部署检查清单

## ✅ 部署前检查

### 1. 环境配置
- [ ] Python 3.8+ 已安装
- [ ] 所有依赖已安装 (`pip install -r requirements.txt`)
- [ ] `.env` 文件已创建
- [ ] `DEEPSEEK_API_KEY` 已设置

### 2. 文件结构
- [ ] `main.py` 存在且已更新
- [ ] `chat.py` 存在
- [ ] `test_continuous_system.py` 存在
- [ ] `data/` 目录存在
- [ ] `docs/CONTINUOUS_THINKING.md` 存在

### 3. 功能测试
```bash
python test_continuous_system.py
```
- [ ] 测试 1: 通信文件管理 - 通过
- [ ] 测试 2: 主动行动评估器 - 通过
- [ ] 测试 3: 系统集成 - 通过
- [ ] 测试 4: 文件结构 - 通过

### 4. 基本运行测试

#### 终端 1 - main.py
```bash
$env:PYTHONIOENCODING='utf-8'
python main.py
```
预期输出：
- [ ] "FakeMan 持续思考系统" 标题
- [ ] 系统初始化成功
- [ ] "开始持续思考循环"
- [ ] 每秒输出思考日志

#### 终端 2 - chat.py
```bash
$env:PYTHONIOENCODING='utf-8'
python chat.py
```
预期输出：
- [ ] "FakeMan 聊天界面" 标题
- [ ] 系统状态显示为 "running"
- [ ] 欲望状态正确显示
- [ ] 可以输入消息

### 5. 交互测试
在 chat.py 中：
```
你: 你好
```
预期行为：
- [ ] 显示 "[FakeMan 正在思考...]"
- [ ] 收到 FakeMan 的回复
- [ ] 回复内容合理
- [ ] 显示思考摘要

### 6. 主动行动测试
- [ ] 等待 60 秒以上
- [ ] 观察是否有主动发言（可能需要多次尝试）
- [ ] 主动发言显示 "💡 [FakeMan 主动发言]"

### 7. 命令测试
在 chat.py 中测试：
- [ ] `state` - 显示系统状态
- [ ] `desires` - 显示欲望状态  
- [ ] `history` - 显示对话历史
- [ ] `quit` - 正常退出

## 🔧 已知问题和解决方案

### Windows 编码问题
**症状**: 中文显示为乱码
**解决方案**: 
```bash
$env:PYTHONIOENCODING='utf-8'
```

### 主动发言不触发
**症状**: AI 从不主动发言
**原因**: 阈值设置过高或时间不够
**解决方案**:
1. 降低 `main.py` 中的阈值
2. 等待更长时间（>120秒）
3. 通过对话改变欲望状态

### 响应超时
**症状**: "[FakeMan 正在思考...]" 后超时
**可能原因**:
1. LLM API 网络问题
2. API 密钥无效
3. main.py 未运行

**解决方案**:
1. 检查网络连接
2. 验证 .env 文件
3. 确保 main.py 在运行

## 📊 性能基准

### 正常运行指标
- CPU 使用率: < 5% (空闲时)
- 内存使用: ~200MB
- 响应时间: 3-10秒（取决于 LLM API）
- 思考频率: 1Hz

### 文件大小
- `user_input.json`: < 1KB
- `ai_output.json`: < 2KB
- `system_state.json`: < 1KB
- `experiences.json`: 随使用增长

## 🚀 部署步骤

### 开发环境
```bash
# 1. 克隆/下载项目
cd fakeman-project

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置
cp .env.example .env  # 如果有模板
# 编辑 .env 添加 API key

# 4. 测试
python test_continuous_system.py

# 5. 运行
# 终端 1
python main.py

# 终端 2  
python chat.py
```

### 生产环境（未来）
```bash
# 使用 supervisor 或 systemd 管理进程
# 使用 nginx 反向代理（如果有 Web UI）
# 配置日志轮转
# 设置监控和告警
```

## 📝 日常维护

### 日志检查
```bash
# 查看主日志
tail -100 data/logs/fakeman.log

# 查看错误
grep ERROR data/logs/fakeman.log
```

### 数据备份
```bash
# 备份经验数据库
cp data/experiences.json data/backup/experiences_$(date +%Y%m%d).json

# 备份日志
tar -czf logs_backup_$(date +%Y%m%d).tar.gz data/logs/
```

### 清理
```bash
# 清理旧日志（保留最近7天）
find data/logs -name "*.log" -mtime +7 -delete

# 清理测试数据
rm -rf data/test_communication/
```

## 🎯 部署后验证

### 冒烟测试
1. [ ] 系统启动无错误
2. [ ] 可以正常对话
3. [ ] 状态查询正常
4. [ ] 日志正常输出
5. [ ] 文件通信正常

### 压力测试（可选）
1. [ ] 连续对话 50 轮
2. [ ] 长时间运行（>1小时）
3. [ ] 多次重启
4. [ ] 异常中断恢复

## 📞 问题报告

如果遇到问题，请收集以下信息：

1. **系统信息**
   - OS 版本
   - Python 版本
   - 依赖版本

2. **日志**
   - `data/logs/fakeman.log` 的最后 100 行
   - 错误堆栈信息

3. **复现步骤**
   - 具体操作步骤
   - 预期行为 vs 实际行为

4. **配置**
   - 是否修改过默认配置
   - 环境变量设置

## ✅ 部署完成确认

完成以下所有项目即表示部署成功：

- [ ] 单元测试全部通过
- [ ] main.py 正常启动并持续运行
- [ ] chat.py 可以正常连接
- [ ] 可以进行正常对话
- [ ] 命令功能正常
- [ ] 日志正常输出
- [ ] 主动行动机制可以触发（至少测试一次）
- [ ] 文档已阅读

## 🎉 部署成功！

系统已准备就绪，开始享受与 FakeMan 的对话吧！

---

*部署清单版本: 1.0*
*最后更新: 2025-10-17*

