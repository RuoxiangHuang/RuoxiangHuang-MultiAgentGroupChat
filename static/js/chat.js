document.addEventListener('DOMContentLoaded', function() {
    const messagesContainer = document.getElementById('messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing');
    const agentSelect = document.getElementById('agent-select');
    const resetButton = document.getElementById('reset-button');
    const smartModeToggle = document.getElementById('smart-mode');
    const agentSelector = document.getElementById('agent-selector');
    const statusIndicator = document.getElementById('status-indicator');
    const dispatcherInfo = document.getElementById('dispatcher-info');
    
    // 存储当前选择的智能体和调度者
    let currentAgent = null;
    let dispatcher = null;
    let availableAgents = [];
    let isSmartMode = false;
    
    // 获取可用的智能体列表
    async function fetchAgents() {
        try {
            const response = await fetch('/agents');
            const data = await response.json();
            
            availableAgents = data.agents;
            dispatcher = data.dispatcher;
            
            // 填充下拉选择框
            agentSelect.innerHTML = '';
            availableAgents.forEach(agent => {
                const option = document.createElement('option');
                option.value = agent.id;
                option.textContent = agent.name;
                option.title = agent.description;
                agentSelect.appendChild(option);
            });
            
            // 设置默认选中的智能体
            if (availableAgents.length > 0) {
                currentAgent = availableAgents[0];
                agentSelect.value = currentAgent.id;
                addMessage(`我是${currentAgent.name}，有什么可以帮助您的吗？`, false, currentAgent.name);
            }
        } catch (error) {
            console.error('Error fetching agents:', error);
            addMessage('无法加载智能体列表，请刷新页面重试', false, '系统');
        }
    }
    
    // 切换智能模式
    smartModeToggle.addEventListener('change', function() {
        isSmartMode = this.checked;
        statusIndicator.textContent = `当前模式：${isSmartMode ? '智能选择' : '手动选择'}`;
        agentSelector.style.display = isSmartMode ? 'none' : 'flex';
        dispatcherInfo.style.display = 'none';
        dispatcherInfo.textContent = '';
        
        if (isSmartMode) {
            addMessage(`已启用智能选择模式，我会根据您的问题自动选择最合适的智能体回答`, false, dispatcher.name);
        } else {
            addMessage(`已回到手动选择模式，您可以自行选择想要对话的智能体`, false, '系统');
        }
    });
    
    // 监听智能体选择变化
    agentSelect.addEventListener('change', function() {
        const selectedId = this.value;
        const selectedName = this.options[this.selectedIndex].text;
        currentAgent = { id: selectedId, name: selectedName };
        addMessage(`我是${selectedName}，有什么可以帮助您的吗？`, false, selectedName);
    });
    
    // 重置当前智能体的对话
    resetButton.addEventListener('click', async function() {
        try {
            await fetch('/reset_conversation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    agent_id: isSmartMode ? null : currentAgent.id,
                    reset_all: isSmartMode
                }),
            });
            
            addMessage(`对话已重置`, false, '系统');
            
            if (isSmartMode) {
                addMessage(`我是${dispatcher.name}，请问有什么可以帮助您的吗？`, false, dispatcher.name);
            } else if (currentAgent) {
                addMessage(`我是${currentAgent.name}，有什么可以帮助您的吗？`, false, currentAgent.name);
            }
        } catch (error) {
            console.error('Error resetting conversation:', error);
            addMessage('重置对话失败，请稍后再试', false, '系统');
        }
    });
    
    // 添加消息到聊天窗口
    function addMessage(text, isUser, agentName) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        if (!isUser && agentName) {
            const agentLabel = document.createElement('div');
            agentLabel.className = 'agent-label';
            agentLabel.textContent = agentName;
            messageDiv.appendChild(agentLabel);
        }
        
        messageDiv.appendChild(document.createTextNode(text));
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // 添加显示调试信息的函数
    function showDebugInfo(debugData) {
        const debugContainer = document.createElement('div');
        debugContainer.className = 'debug-info';
        debugContainer.style.border = '1px dashed #ccc';
        debugContainer.style.padding = '8px';
        debugContainer.style.margin = '5px 0';
        debugContainer.style.backgroundColor = '#f9f9f9';
        debugContainer.style.fontSize = '0.85em';
        debugContainer.style.color = '#666';
        
        let debugHtml = `<strong>🔍 调试信息:</strong><br>`;
        debugHtml += `分析结果: ${debugData.analysis}<br>`;
        debugHtml += `完整响应: ${debugData.full_response}<br>`;
        
        if (debugData.current_speaker) {
            debugHtml += `当前发言者: ${debugData.current_speaker.name}<br>`;
        }
        
        debugHtml += `输入消息: ${debugData.input_message.character_name}: ${debugData.input_message.message}<br>`;
        
        debugContainer.innerHTML = debugHtml;
        dispatcherInfo.appendChild(debugContainer);
    }
    
    // 智能选择模式下的消息处理
    async function handleSmartMode(message) {
        typingIndicator.style.display = 'block';
        addMessage(`正在为您智能选择最适合回答的智能体...`, false, dispatcher.name);
        
        try {
            // 首先调用调度者进行分发
            const dispatchResponse = await fetch('/dispatch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
            });
            
            const dispatchData = await dispatchResponse.json();
            const selectedAgent = dispatchData.selected_agent;
            
            // 显示调度结果
            dispatcherInfo.style.display = 'block';
            dispatcherInfo.innerHTML = `<strong>🔄 用户发言对象分析:</strong> ${dispatchData.dispatcher_analysis || "未返回分析结果"}`;
            
            // 使用选定的智能体回答问题
            const chatResponse = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    message,
                    agent_id: selectedAgent.id,
                    smart_mode: true,
                    auto_continue: true
                }),
            });
            
            const chatData = await chatResponse.json();
            typingIndicator.style.display = 'none';
            
            // 添加所选智能体的回复
            addMessage(chatData.response, false, chatData.agent.name);
            
            // 如果有下一个发言者，显示相关调试信息
            if (chatData.next_speaker && chatData.next_speaker.type === 'agent') {
                // 显示角色发言目标检测结果
                dispatcherInfo.innerHTML += `<br><strong>🎭 角色发言目标检测:</strong> ${chatData.dispatcher_analysis || "未返回检测结果"}`;
                
                // 如果有调试信息，显示它
                if (chatData.debug_info) {
                    showDebugInfo(chatData.debug_info);
                }
                
                // 自动进行下一个角色的回复
                setTimeout(async () => {
                    try {
                        typingIndicator.style.display = 'block';
                        const nextSpeakerResponse = await fetch('/chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ 
                                message: `请针对前面的对话内容进行回复`,
                                agent_id: chatData.next_speaker.id,
                                auto_continue: true
                            }),
                        });
                        
                        const nextSpeakerData = await nextSpeakerResponse.json();
                        typingIndicator.style.display = 'none';
                        
                        // 添加下一个角色的回复
                        addMessage(nextSpeakerData.response, false, nextSpeakerData.agent.name);
                        
                        // 如果还有下一个发言者，显示调试信息
                        if (nextSpeakerData.next_speaker && nextSpeakerData.debug_info) {
                            dispatcherInfo.innerHTML += `<br><strong>🎭 角色发言目标检测:</strong> ${nextSpeakerData.dispatcher_analysis || "未返回检测结果"}`;
                            showDebugInfo(nextSpeakerData.debug_info);
                        }
                    } catch (error) {
                        console.error('Error with next speaker:', error);
                        typingIndicator.style.display = 'none';
                    }
                }, 1000);
            }
        } catch (error) {
            console.error('Error in smart mode:', error);
            typingIndicator.style.display = 'none';
            addMessage('智能选择过程中出现错误，请稍后再试', false, '系统');
        }
    }

    // 发送消息并获取回复
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        addMessage(message, true);
        userInput.value = '';
        typingIndicator.style.display = 'block';
        
        // 根据当前模式处理消息
        if (isSmartMode) {
            await handleSmartMode(message);
        } else {
            // 常规模式，直接调用选定的智能体
            if (!currentAgent) {
                typingIndicator.style.display = 'none';
                addMessage('请先选择一个智能体', false, '系统');
                return;
            }
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        message, 
                        agent_id: currentAgent.id,
                        auto_continue: true // 启用自动继续对话功能
                    }),
                });

                const data = await response.json();
                typingIndicator.style.display = 'none';
                
                // 添加智能体回复
                addMessage(data.response, false, data.agent.name);
                
                // 如果有下一个发言者，显示相关调试信息
                if (data.next_speaker) {
                    // 显示调度结果
                    dispatcherInfo.style.display = 'block';
                    dispatcherInfo.innerHTML = `<strong>🎭 角色发言目标检测:</strong> ${data.dispatcher_analysis || "未返回检测结果"}`;
                    
                    // 如果有调试信息，显示它
                    if (data.debug_info) {
                        showDebugInfo(data.debug_info);
                    }
                    
                    // 如果下一个发言者是角色，自动进行对话
                    if (data.next_speaker.type === 'agent') {
                        setTimeout(async () => {
                            try {
                                typingIndicator.style.display = 'block';
                                const nextSpeakerResponse = await fetch('/chat', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                    },
                                    body: JSON.stringify({ 
                                        message: `请针对前面的对话内容进行回复`,
                                        agent_id: data.next_speaker.id,
                                        auto_continue: true
                                    }),
                                });
                                
                                const nextSpeakerData = await nextSpeakerResponse.json();
                                typingIndicator.style.display = 'none';
                                
                                // 添加下一个角色的回复
                                addMessage(nextSpeakerData.response, false, nextSpeakerData.agent.name);
                                
                                // 如果还有下一个发言者，显示调试信息
                                if (nextSpeakerData.next_speaker && nextSpeakerData.debug_info) {
                                    dispatcherInfo.innerHTML += `<br><strong>🎭 角色发言目标检测:</strong> ${nextSpeakerData.dispatcher_analysis || "未返回检测结果"}`;
                                    showDebugInfo(nextSpeakerData.debug_info);
                                }
                            } catch (error) {
                                console.error('Error with next speaker:', error);
                                typingIndicator.style.display = 'none';
                            }
                        }, 1000);
                    }
                }
            } catch (error) {
                console.error('Error:', error);
                typingIndicator.style.display = 'none';
                addMessage('抱歉，出现了错误，请稍后再试。', false, '系统');
            }
        }
    }

    // 事件监听
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // 初始化加载智能体列表
    fetchAgents();
}); 