# Coze 多智能体对话 Web 应用

这是一个基于 Flask 框架的 Web 应用，用于与 Coze 平台多个 Agent 进行对话。

## 功能特点

- 多智能体支持，可以选择不同的智能体进行对话
- 智能选择功能，自动根据问题分配最适合的智能体
- 为每个智能体独立维护对话上下文
- 实时响应显示
- 简洁美观的界面设计
- 支持重置特定智能体或所有对话历史

## 项目结构

```
├── app.py           # 主应用和路由
├── config.py        # 配置文件（智能体和API设置）
├── dispatcher.py    # 调度相关逻辑
├── requirements.txt # 依赖包
├── static/          # 静态资源
└── templates/       # HTML模板
    └── index.html   # 主页模板
```

## 安装步骤

1. 克隆或下载此仓库

2. 安装依赖包

```bash
pip install -r requirements.txt
```

3. 设置环境变量（可选）

如果需要使用非默认的 Coze API 地址，可以创建一个 `.env` 文件并设置：

```
COZE_API_BASE=你的API地址
```

## 运行应用

```bash
python app.py
```

应用将在本地运行，访问 http://127.0.0.1:5000/ 即可使用。

## 自定义设置

在 `config.py` 文件中，您可以修改以下参数：

- `COZE_API_TOKEN`: 您的 Coze API 令牌
- `AVAILABLE_AGENTS`: 定义可用的智能体列表，包括ID、名称和描述
  
```python
AVAILABLE_AGENTS = [
    {
        "id": "您的Bot ID",
        "name": "智能体名称",
        "description": "智能体描述"
    },
    # 添加更多智能体...
]
```

- `DISPATCHER_AGENT`: 调度者智能体的配置

```python
DISPATCHER_AGENT = {
    "id": "您的调度者Bot ID",
    "name": "智能调度员",
    "description": "根据用户问题选择合适的智能体"
}
```

## 调度逻辑扩展

如需自定义或扩展调度逻辑，可以修改 `dispatcher.py` 文件中的相关函数：

- `build_dispatch_prompt`: 定义发送给调度者的提示词
- `extract_agent_from_response`: 从调度者回复中提取智能体信息
- `extract_analysis`: 提取并格式化调度分析结果
- `process_dispatch`: 整体调度处理流程

## 使用方法

应用支持两种对话模式：

### 手动选择模式
1. 从界面顶部的下拉菜单选择要对话的智能体
2. 在输入框中输入问题并点击发送
3. 如果要重置当前智能体的对话历史，点击"重置对话"按钮

### 智能选择模式
1. 点击界面顶部的"智能选择"开关启用智能选择功能
2. 在输入框中输入任何问题
3. 系统会自动调用调度者智能体分析您的问题
4. 调度者会选择最适合回答您问题的智能体
5. 所选智能体会自动回复您的问题
6. 对话上方会显示智能选择的结果信息

## 注意事项

- 本应用使用会话（Session）来保持对话上下文，请确保浏览器允许 Cookie
- 每个智能体的对话上下文是独立的
- 智能选择模式下，可以一键重置所有智能体的对话历史
- 对于生产环境部署，请在 config.py 中设置更安全的 `SESSION_SECRET` 