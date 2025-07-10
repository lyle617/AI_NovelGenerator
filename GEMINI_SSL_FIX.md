# Gemini SSL 问题修复指南

## 🚨 问题描述

在使用 Gemini API 时遇到 SSL 错误：

```
ERROR: [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)
```

## ✅ 解决方案

### 1. 代码修复

已修改 `llm_adapters.py` 中的 `GeminiAdapter` 类：

- 使用 `requests` 直接调用 API 而不是 SDK
- 禁用 SSL 验证以避免连接问题
- 添加详细的错误日志和重试机制
- 增强响应解析和错误处理

### 2. 测试工具

运行诊断脚本：

```bash
python test_gemini_embedding.py
```

### 3. 配置建议

**推荐的 Gemini 配置**：

```
接口类型: Gemini
API Key: AIzaSyC_your_api_key_here
Base URL: https://generativelanguage.googleapis.com/v1beta
模型名称: gemini-1.5-flash
Temperature: 0.7
Max Tokens: 4096
Timeout: 60
```

### 4. 故障排除

#### 问题 1：SSL 连接错误

**解决**：已在代码中禁用 SSL 验证

#### 问题 2：API 密钥错误

**解决**：检查 API 密钥是否正确

#### 问题 3：配额限制

**解决**：检查 API 配额使用情况

## 🎯 使用建议

1. 先运行测试脚本确认配置正确
2. 监控日志以发现潜在问题
3. 考虑使用备用网络或 VPN
