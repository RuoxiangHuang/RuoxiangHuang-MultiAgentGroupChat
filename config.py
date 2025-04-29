# 智能体配置
AVAILABLE_AGENTS = [
    {
        "id": "7491319002259128320",
        "name": "神秘侦探",
        "description": "擅长推理和分析线索的侦探角色"
    },
    {
        "id": "7494275236897619994",
        "name": "疑似嫌犯",
        "description": "行为可疑且有重要线索的角色"
    },
    {
        "id": "7494275547825602594",
        "name": "知情目击者",
        "description": "目睹了案件关键情节的证人角色"
    }
]

# 调度者智能体配置
USER_DISPATCHER_AGENT = {
    "id": "7494277340248211490",
    "name": "用户发言对象检测",
    "description": "基于用户发言识别发言对象"
}

# 智能体发言对象检测智能体配置
CHARACTER_DISPATCHER_AGENT = {
    "id": "7495228391927332891",  # 注意：实际使用时需要替换为新创建的智能体ID
    "name": "智能体发言对象检测",
    "description": "基于智能体发言识别发言对象"
}

# API配置
COZE_API_TOKEN = "pat_STpwD8k0FA2cwzSubS8pydC0dbmu6ARilhJ2TTdo7ucM1WkTmVnIZP9cR45RmRry"

# 会话密钥（生产环境应改为强随机值）
# SESSION_SECRET = os.urandom(24)  # 实际应用中设置 