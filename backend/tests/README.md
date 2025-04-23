# 测试说明

本目录包含了对修改后的代理功能和API端点的测试用例。

## 测试文件

- `test_agents.py`: 测试修改后的代理功能
- `test_api_endpoints.py`: 测试API端点
- `test_para_manager_exchange.py`: 测试前端和后端段落管理器数据交换
- `test_format_fixer.py`: 测试格式修复功能
- `run_tests.py`: 运行所有测试的脚本

## 运行测试

### 运行不需要服务器的测试

```bash
python run_tests.py
```

### 运行所有测试（包括需要服务器的测试）

```bash
python run_tests.py --with-server
```

注意：运行需要服务器的测试前，请确保服务器已经启动。

## 测试内容

### 1. 测试段落格式检查功能

测试FormatAgent的段落分析功能，确保能够正确识别格式错误。

### 2. 测试段落格式修复功能

测试FormatAgent的段落管理器修复功能，确保能够正确应用格式。

### 3. 测试段落内容增强功能

测试EditorAgent的段落管理器增强功能，确保能够提供有用的内容改进。

### 4. 测试前端和后端段落管理器数据交换

测试前端和后端段落管理器数据交换，确保数据能够正确传递。

### 5. 测试新添加的API端点

测试新添加的API端点，确保能够正确响应请求。

## 测试结果说明

测试成功时，会显示类似以下的输出：

```
Ran X tests in X.XXXs

OK
```

测试失败时，会显示类似以下的输出：

```
Ran X tests in X.XXXs

FAILED (failures=X, errors=X)
```

并且会显示具体的失败原因。
