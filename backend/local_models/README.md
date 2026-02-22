# 本地模型使用指南

## 推荐模型

| 模型 | 量化格式 | 内存占用 | 推荐场景 |
|------|---------|---------|---------|
| Qwen2.5-1.5B-Instruct | GGUF q4_0 | ~2GB | 段落分类、轻量任务 |
| Qwen2.5-3B-Instruct | GGUF q4_0 | ~3.5GB | 格式分析、内容增强 |
| Llama3.1-2B-Instruct | GGUF q4_0 | ~2GB | 通用对话 |

## Ollama 快速开始

```bash
# 1. 安装 Ollama
# 下载地址: https://ollama.com/download

# 2. 拉取模型
ollama pull qwen2.5:1.5b

# 3. 在 keys.json 中配置 ollama provider
# 复制 keys.json.example 为 keys.json，确保 ollama provider 配置正确
# 然后设置 agent 使用 ollama_qwen2.5 模型
```

配置示例（keys.json）：
```json
{
  "providers": {
    "ollama": {
      "type": "ollama",
      "base_url": "http://localhost:11434/v1",
      "models": {
        "qwen2.5": "qwen2.5:1.5b"
      }
    }
  }
}
```

## llama.cpp 快速开始

```bash
# 1. 下载 GGUF 模型
# 从 Hugging Face 下载: Qwen/Qwen2.5-1.5B-Instruct-GGUF
# 或使用镜像站: https://modelscope.cn/models

# 2. 放置在 backend/local_models/ 目录

# 3. 安装依赖
pip install llama-cpp-python

# 4. 在 keys.json 中配置模型路径
```

配置示例（keys.json）：
```json
{
  "providers": {
    "llamacpp": {
      "type": "llamacpp",
      "model_path": "./local_models/qwen2.5-1.5b-instruct-q4_0.gguf",
      "n_ctx": 4096,
      "n_threads": 4,
      "n_gpu_layers": 0,
      "verbose": false,
      "models": {
        "qwen2.5-1.5b": "qwen2.5-1.5b-instruct"
      }
    }
  }
}
```

## ONNX Runtime 快速开始

```bash
# 1. 安装依赖
pip install optimum[onnxruntime] transformers torch

# 2. 导出 ONNX 模型
optimum-cli export onnx --model Qwen/Qwen2.5-1.5B-Instruct --task text-generation-with-past ./qwen2.5-1.5b-onnx/

# 3. 在 keys.json 中配置模型路径
```

配置示例（keys.json）：
```json
{
  "providers": {
    "onnx": {
      "type": "onnx",
      "model_path": "./local_models/qwen2.5-1.5b-instruct-onnx/",
      "providers": ["CPUExecutionProvider"],
      "models": {
        "qwen2.5-onnx": "qwen2.5-1.5b-instruct-onnx"
      }
    }
  }
}
```

## 模型使用方式

在代码中使用本地模型：

```python
from agents.setting import LLMs

llms = LLMs()
# 使用 Ollama
llms.set_model('ollama_qwen2.5')

# 或使用 llama.cpp
llms.set_model('llamacpp_qwen2.5-1.5b')

# 或使用 ONNX
llms.set_model('onnx_qwen2.5-onnx')

# 调用
response = llms.chat_completions_create(
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

## 切换 Agent 使用的模型

修改 `backend/agent_models.json`：

```json
{
  "format": "ollama_qwen2.5",
  "editor": "ollama_qwen2.5",
  "advice": "ollama_qwen2.5",
  "communicate": "ollama_qwen2.5"
}
```

## 性能基准测试

| 指标 | 云端 | 本地 (Qwen2.5-1.5B) |
|------|------|---------------------|
| 首字延迟 | ~300ms | ~100-200ms |
| 生成速度 | ~30 tokens/s | ~10-20 tokens/s |
| 内存占用 | - | ~2-3GB |
| 网络依赖 | 必需 | 不需要 |
