# Ollama 长文本处理优化配置指南

## 🚀 当前模型信息
- **模型**: medgemma:latest (27.0B参数)
- **上下文长度**: 131,072 tokens (~500KB文本)
- **架构**: Gemma3

## ⚙️ 优化配置参数

### 1. 基本配置优化
```bash
# 设置环境变量增加内存限制
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_QUEUE=10

# 重启Ollama服务
ollama serve
```

### 2. API请求优化参数
```json
{
  "model": "medgemma:latest",
  "options": {
    "num_ctx": 8192,          // 上下文窗口 (最大131072)
    "num_predict": 4096,      // 输出长度限制
    "temperature": 0.1,       // 降低随机性
    "top_p": 0.9,            // 核采样
    "top_k": 40,             // Top-K采样
    "repeat_penalty": 1.1,    // 重复惩罚
    "stop": ["```\n\n", "```\n", "\n\n---"]  // 停止标记
  },
  "timeout": 600             // 10分钟超时
}
```

### 3. 系统级优化

#### macOS优化
```bash
# 增加文件描述符限制
ulimit -n 4096

# 检查可用内存
vm_stat | grep "Pages free"

# 监控Ollama进程
top -pid $(pgrep ollama)
```

#### 内存优化
```bash
# 清理系统缓存
sudo purge

# 检查Ollama内存使用
ps aux | grep ollama
```

## 📊 性能基准测试

### 输入长度测试
- **短文本** (< 500字符): 10-30秒
- **中等文本** (500-2000字符): 30-90秒  
- **长文本** (2000-5000字符): 90-300秒
- **超长文本** (> 5000字符): 300-600秒

### 优化建议
1. **分段处理**: 超过2000字符的报告考虑分段
2. **缓存策略**: 相似报告可以复用部分结果
3. **并行处理**: 多个短报告并行处理
4. **流式输出**: 使用stream模式获得实时反馈

## 🔧 故障排除

### 常见问题
1. **超时错误**: 增加timeout参数
2. **内存不足**: 减少num_ctx或重启Ollama
3. **输出截断**: 增加num_predict参数
4. **JSON解析失败**: 添加更多停止标记

### 调试命令
```bash
# 检查Ollama状态
ollama list

# 查看模型详情
ollama show medgemma:latest

# 监控资源使用
htop -p $(pgrep ollama)

# 查看Ollama日志
tail -f ~/.ollama/logs/server.log
```

## 📈 性能监控

### 关键指标
- **处理时间**: 目标 < 120秒
- **内存使用**: < 16GB
- **CPU使用率**: < 80%
- **输出质量**: JSON解析成功率 > 95%

### 监控脚本
```python
import psutil
import time

def monitor_ollama():
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
        if 'ollama' in proc.info['name']:
            print(f"PID: {proc.info['pid']}")
            print(f"内存: {proc.info['memory_info'].rss / 1024 / 1024:.1f} MB")
            print(f"CPU: {proc.info['cpu_percent']:.1f}%")
```

## 🎯 最佳实践

1. **预热模型**: 首次使用前发送简单请求
2. **批量处理**: 相似类型报告一起处理
3. **错误重试**: 实现指数退避重试机制
4. **结果缓存**: 缓存常见模式的结果
5. **监控告警**: 设置性能阈值告警

## 📝 配置模板

### 生产环境配置
```python
OLLAMA_CONFIG = {
    "model": "medgemma:latest",
    "options": {
        "num_ctx": 8192,
        "num_predict": 4096,
        "temperature": 0.1,
        "top_p": 0.9,
        "repeat_penalty": 1.1
    },
    "timeout": 600,
    "max_retries": 3,
    "retry_delay": 5
}
```

### 开发环境配置
```python
OLLAMA_CONFIG_DEV = {
    "model": "medgemma:latest", 
    "options": {
        "num_ctx": 4096,
        "num_predict": 2048,
        "temperature": 0.2
    },
    "timeout": 300,
    "max_retries": 1
}
``` 