import re
from cozepy import Message, ChatEventType

class Agent:
    """基础智能体类"""
    def __init__(self, coze, agent_info, user_id):
        self.coze = coze
        self.id = agent_info['id']
        self.name = agent_info['name']
        self.description = agent_info.get('description', '')
        self.user_id = user_id
        
    def get_info(self):
        """获取智能体信息"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }
    
    def chat(self, user_message, conversation_id=None):
        """与智能体对话"""
        response_text = ""
        new_conversation_id = None
        
        for event in self.coze.chat.stream(
            bot_id=self.id,
            user_id=self.user_id,
            additional_messages=[Message.build_user_question_text(user_message)],
            conversation_id=conversation_id
        ):
            if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                response_text += event.message.content
            
            if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
                if hasattr(event.chat, 'conversation_id'):
                    new_conversation_id = event.chat.conversation_id
        
        return {
            'response': response_text,
            'new_conversation_id': new_conversation_id
        }

class CharacterAgent(Agent):
    """角色智能体类"""
    def __init__(self, coze, agent_info, user_id, speaking_willingness=5):
        super().__init__(coze, agent_info, user_id)
        # 验证发言意愿度在1-10范围内
        if not isinstance(speaking_willingness, int) or speaking_willingness < 1 or speaking_willingness > 10:
            raise ValueError("发言意愿度必须是1-10范围内的整数")
        self.speaking_willingness = speaking_willingness
    
    def get_info(self):
        """获取智能体信息，包含发言意愿度"""
        info = super().get_info()
        info['speaking_willingness'] = self.speaking_willingness
        return info

class DispatcherAgent(Agent):
    """调度者智能体类"""
    def __init__(self, coze, agent_info, user_id, available_agents):
        super().__init__(coze, agent_info, user_id)
        self.available_agents = available_agents
        self.initialized = False
    
    def build_agents_list_prompt(self):
        """构建发送给调度者的可用智能体列表提示词"""
        agent_info = ""
        for agent in self.available_agents:
            agent_info += f"{agent.name}：{agent.description}（ID: {agent.id}）\n"
        
        # 仅提供智能体列表信息，其他提示词在Coze平台上已配置
        prompt = f"""可用的智能体有：
{agent_info}"""
        
        return prompt
    
    def build_user_message_prompt(self, user_message):
        """构建发送给调度者的用户消息提示词"""
        return user_message
    
    def build_character_message_prompt(self, character_name, character_message):
        """构建发送给角色发言对象调度者的角色消息提示词"""
        prompt = f"{character_name}：{character_message}"
        return prompt
    
    def extract_agent_from_response(self, response):
        """从调度者回复中提取选定的智能体"""
        response = response.strip()
        
        # 初始化阶段，返回None
        if response == "OK":
            return None
            
        # 直接通过名称匹配
        for agent in self.available_agents:
            if agent.name == response:
                return agent
                
        # 如果没有精确匹配，尝试模糊匹配
        for agent in self.available_agents:
            if agent.name in response:
                return agent
        
        # 如果仍然找不到，返回第一个智能体作为默认
        return self.available_agents[0] if self.available_agents else None
    
    def extract_next_speaker(self, response, current_speaker):
        """从角色发言对象调度者的回复中提取下一个发言者"""
        response = response.strip()
        
        # 初始化阶段，返回None
        if response == "OK":
            return None, "已初始化智能体发言对象检测"
        
        # 检查是否为用户
        if response == "用户":
            return "user", "用户将进行下一轮发言"
        
        # 检查是否为错误
        if response == "error":
            return "user", "检测发生错误，默认由用户进行下一轮发言"
        
        # 检查是否为当前发言者（不应允许选择当前发言者）
        if current_speaker and current_speaker.name == response:
            return "user", f"不应选择当前发言者（{current_speaker.name}）作为下一个发言者，默认由用户进行下一轮发言"
            
        # 直接通过名称匹配
        for agent in self.available_agents:
            if agent.name == response:
                return agent, f"下一个发言者将是「{agent.name}」"
                
        # 如果没有精确匹配，尝试模糊匹配
        for agent in self.available_agents:
            if agent.name in response:
                return agent, f"下一个发言者可能是「{agent.name}」"
        
        # 如果仍然找不到，返回用户作为默认
        return "user", "无法确定下一个发言者，默认由用户进行下一轮发言"
    
    def dispatch(self, user_message, conversation_id=None):
        """处理用户发言对象调度请求，返回选定的智能体和分析结果"""
        # 首次调用时，初始化调度者
        if not self.initialized:
            # 构建智能体列表提示词
            prompt = self.build_agents_list_prompt()
            
            # 调用调度者智能体
            chat_result = self.chat(prompt, conversation_id)
            response_text = chat_result['response']
            new_conversation_id = chat_result['new_conversation_id']
            
            # 验证初始化响应
            if "OK" in response_text:
                self.initialized = True
                conversation_id = new_conversation_id
            
        # 发送用户消息
        prompt = self.build_user_message_prompt(user_message)
        
        # 调用调度者智能体
        chat_result = self.chat(prompt, conversation_id)
        response_text = chat_result['response']
        new_conversation_id = chat_result['new_conversation_id']
        
        # 提取被选中的智能体
        selected_agent = self.extract_agent_from_response(response_text)
        
        # 如果未能提取到智能体，使用第一个作为默认
        if not selected_agent and self.available_agents:
            selected_agent = self.available_agents[0]
            dispatcher_analysis = f"无法确定最佳智能体，默认使用：{selected_agent.name}"
        else:
            # 用回复作为分析（回复就是智能体名称）
            dispatcher_analysis = f"已选择「{response_text}」回答您的问题"
        
        return {
            'selected_agent': selected_agent,
            'dispatcher_analysis': dispatcher_analysis,
            'new_conversation_id': new_conversation_id,
            'full_response': response_text
        }
    
    def dispatch_next_speaker(self, character_name, character_message, conversation_id=None, current_speaker=None):
        """处理角色发言对象调度请求，返回下一个发言者"""
        # 首次调用时，初始化调度者
        if not self.initialized:
            # 构建智能体列表提示词
            prompt = self.build_agents_list_prompt()
            
            # 调用调度者智能体
            chat_result = self.chat(prompt, conversation_id)
            response_text = chat_result['response']
            new_conversation_id = chat_result['new_conversation_id']
            
            # 验证初始化响应
            if "OK" in response_text:
                self.initialized = True
                conversation_id = new_conversation_id
            
        # 构建角色消息提示词
        prompt = self.build_character_message_prompt(character_name, character_message)
        
        # 调用调度者智能体
        chat_result = self.chat(prompt, conversation_id)
        response_text = chat_result['response']
        new_conversation_id = chat_result['new_conversation_id']
        
        # 提取下一个发言者
        next_speaker, analysis = self.extract_next_speaker(response_text, current_speaker)
        
        return {
            'next_speaker': next_speaker,
            'dispatcher_analysis': analysis,
            'new_conversation_id': new_conversation_id,
            'full_response': response_text
        } 