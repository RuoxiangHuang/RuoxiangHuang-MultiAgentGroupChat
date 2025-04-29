from flask import Flask, render_template, request, jsonify, session
import os
from cozepy import Coze, TokenAuth, Message, ChatEventType, COZE_CN_BASE_URL
from agent import Agent, CharacterAgent, DispatcherAgent  # 导入新的智能体类
from config import AVAILABLE_AGENTS, USER_DISPATCHER_AGENT, CHARACTER_DISPATCHER_AGENT, COZE_API_TOKEN  # 导入配置

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Initialize Coze client
coze_api_token = COZE_API_TOKEN
coze_api_base = os.getenv("COZE_API_BASE") or COZE_CN_BASE_URL
coze = Coze(auth=TokenAuth(coze_api_token), base_url=coze_api_base)

# 全局变量保存调度者实例
global_dispatcher = None
global_character_dispatcher = None

def get_user_id():
    """获取或创建用户ID"""
    if 'user_id' not in session:
        session['user_id'] = str(os.urandom(8).hex())
    return session['user_id']

def initialize_agents():
    """初始化智能体实例"""
    global global_dispatcher, global_character_dispatcher
    user_id = get_user_id()
    character_agents = [CharacterAgent(coze, agent_info, user_id) for agent_info in AVAILABLE_AGENTS]
    
    # 检查全局调度者是否已经初始化
    if global_dispatcher is None:
        global_dispatcher = DispatcherAgent(coze, USER_DISPATCHER_AGENT, user_id, character_agents)
    
    # 检查全局角色发言对象检测智能体是否已经初始化
    if global_character_dispatcher is None:
        global_character_dispatcher = DispatcherAgent(coze, CHARACTER_DISPATCHER_AGENT, user_id, character_agents)
    
    return character_agents, global_dispatcher

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/agents', methods=['GET'])
def get_agents():
    """返回可用的智能体列表和调度者"""
    character_agents, dispatcher = initialize_agents()
    return jsonify({
        "agents": [agent.get_info() for agent in character_agents],
        "dispatcher": dispatcher.get_info(),
        "character_dispatcher": global_character_dispatcher.get_info()
    })

@app.route('/dispatch', methods=['POST'])
def dispatch():
    """根据用户问题调用调度者智能体选择合适的回答智能体"""
    data = request.json
    user_message = data.get('message', '')
    
    # 获取调度者会话ID
    dispatcher_conversation_key = f"conversation_id_dispatcher"
    dispatcher_conversation_id = session.get(dispatcher_conversation_key)
    
    # 初始化智能体
    character_agents, dispatcher = initialize_agents()
    
    # 调用调度处理函数
    dispatch_result = dispatcher.dispatch(
        user_message=user_message,
        conversation_id=dispatcher_conversation_id
    )
    
    # 保存新的会话ID
    if dispatch_result['new_conversation_id']:
        session[dispatcher_conversation_key] = dispatch_result['new_conversation_id']
    
    # 获取选中智能体的信息
    selected_agent = dispatch_result['selected_agent']
    selected_agent_info = selected_agent.get_info() if selected_agent else None
    
    return jsonify({
        'selected_agent': selected_agent_info,
        'dispatcher_analysis': dispatch_result['dispatcher_analysis']
    })

@app.route('/dispatch_next_speaker', methods=['POST'])
def dispatch_next_speaker():
    """根据角色回复确定下一个发言者（用户或其他角色）"""
    data = request.json
    character_name = data.get('character_name', '')
    character_message = data.get('character_message', '')
    current_speaker_id = data.get('current_speaker_id', '')
    
    # 获取角色发言对象调度者会话ID
    character_dispatcher_conversation_key = f"conversation_id_character_dispatcher"
    character_dispatcher_conversation_id = session.get(character_dispatcher_conversation_key)
    
    # 初始化智能体
    character_agents, _ = initialize_agents()
    
    # 获取当前发言者
    current_speaker = None
    if current_speaker_id:
        current_speaker = next((agent for agent in character_agents if agent.id == current_speaker_id), None)
    
    # 调用角色发言对象调度处理函数
    dispatch_result = global_character_dispatcher.dispatch_next_speaker(
        character_name=character_name,
        character_message=character_message,
        conversation_id=character_dispatcher_conversation_id,
        current_speaker=current_speaker
    )
    
    # 保存新的会话ID
    if dispatch_result['new_conversation_id']:
        session[character_dispatcher_conversation_key] = dispatch_result['new_conversation_id']
    
    # 获取下一个发言者的信息
    next_speaker = dispatch_result['next_speaker']
    
    # 如果下一个发言者是用户
    if next_speaker == "user":
        next_speaker_info = {
            'id': 'user',
            'name': '用户',
            'type': 'user'
        }
    # 如果下一个发言者是智能体
    elif next_speaker:
        next_speaker_info = next_speaker.get_info()
        next_speaker_info['type'] = 'agent'
    else:
        next_speaker_info = None
    
    # 增加输出完整响应内容，便于调试
    debug_info = {
        'analysis': dispatch_result['dispatcher_analysis'],
        'full_response': dispatch_result.get('full_response', ''),
        'current_speaker': current_speaker.get_info() if current_speaker else None,
        'input_message': {
            'character_name': character_name,
            'message': character_message
        }
    }
    
    return jsonify({
        'next_speaker': next_speaker_info,
        'dispatcher_analysis': dispatch_result['dispatcher_analysis'],
        'debug_info': debug_info
    })

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    agent_id = data.get('agent_id')
    smart_mode = data.get('smart_mode', False)
    auto_continue = data.get('auto_continue', False)  # 是否自动继续角色对话
    
    # 如果启用智能模式，则直接返回结果，因为前端会先调用/dispatch
    if smart_mode and not agent_id:
        return jsonify({
            'response': '请稍等，正在为您智能选择最合适的智能体...',
            'agent': {
                'id': 'system',
                'name': '系统'
            },
            'next_speaker': None
        })
    
    # 初始化智能体
    character_agents, dispatcher = initialize_agents()
    
    # 如果没有指定agent_id，使用默认的第一个智能体
    if not agent_id:
        current_agent = character_agents[0]
    else:
        # 查找指定ID的智能体
        current_agent = next((agent for agent in character_agents if agent.id == agent_id), None)
        # 如果是调度者
        if not current_agent and agent_id == dispatcher.id:
            current_agent = dispatcher
        # 如果仍然找不到，使用第一个智能体
        if not current_agent:
            current_agent = character_agents[0]
    
    # 为每个智能体维护独立的会话
    conversation_key = f"conversation_id_{current_agent.id}"
    conversation_id = session.get(conversation_key)
    
    # 与智能体对话
    chat_result = current_agent.chat(user_message, conversation_id)
    response_text = chat_result['response']
    
    # 保存会话ID
    if chat_result['new_conversation_id']:
        session[conversation_key] = chat_result['new_conversation_id']
    
    # 如果启用自动继续对话且当前智能体是角色智能体
    next_speaker = None
    dispatcher_analysis = None
    debug_info = None
    
    if auto_continue and isinstance(current_agent, CharacterAgent):
        # 获取角色发言对象调度者会话ID
        character_dispatcher_conversation_key = f"conversation_id_character_dispatcher"
        character_dispatcher_conversation_id = session.get(character_dispatcher_conversation_key)
        
        # 调用角色发言对象检测
        dispatch_result = global_character_dispatcher.dispatch_next_speaker(
            character_name=current_agent.name,
            character_message=response_text,
            conversation_id=character_dispatcher_conversation_id,
            current_speaker=current_agent
        )
        
        # 保存新的会话ID
        if dispatch_result['new_conversation_id']:
            session[character_dispatcher_conversation_key] = dispatch_result['new_conversation_id']
        
        # 获取下一个发言者的信息
        next_speaker = dispatch_result['next_speaker']
        
        # 保存分析结果
        dispatcher_analysis = dispatch_result['dispatcher_analysis']
        
        # 如果有调试信息，也保存它
        if 'debug_info' in dispatch_result:
            debug_info = dispatch_result['debug_info']
        
        # 如果下一个发言者是用户
        if next_speaker == "user":
            next_speaker = {
                'id': 'user',
                'name': '用户',
                'type': 'user'
            }
        # 如果下一个发言者是智能体
        elif next_speaker:
            next_speaker_info = next_speaker.get_info()
            next_speaker_info['type'] = 'agent'
            next_speaker = next_speaker_info
    
    return jsonify({
        'response': response_text,
        'agent': current_agent.get_info(),
        'next_speaker': next_speaker,
        'dispatcher_analysis': dispatcher_analysis,
        'debug_info': debug_info
    })

@app.route('/reset_conversation', methods=['POST'])
def reset_conversation():
    """重置特定智能体的会话"""
    global global_dispatcher, global_character_dispatcher
    data = request.json
    agent_id = data.get('agent_id')
    reset_all = data.get('reset_all', False)
    
    if reset_all:
        # 重置所有会话，包括调度者
        for key in list(session.keys()):
            if key.startswith('conversation_id_'):
                session.pop(key)
        # 重置全局调度者实例
        global_dispatcher = None
        global_character_dispatcher = None
    elif agent_id:
        conversation_key = f"conversation_id_{agent_id}"
        if conversation_key in session:
            session.pop(conversation_key)
        # 如果重置调度者，也重置全局实例
        if agent_id == USER_DISPATCHER_AGENT['id']:
            global_dispatcher = None
        # 如果重置角色发言对象检测智能体，也重置全局实例
        if agent_id == CHARACTER_DISPATCHER_AGENT['id']:
            global_character_dispatcher = None
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True) 