import os

from cozepy import Coze, TokenAuth, Message, ChatEventType, COZE_CN_BASE_URL

# initialize client
coze_api_token = "pat_STpwD8k0FA2cwzSubS8pydC0dbmu6ARilhJ2TTdo7ucM1WkTmVnIZP9cR45RmRry"
coze_api_base = os.getenv("COZE_API_BASE") or COZE_CN_BASE_URL
coze = Coze(auth=TokenAuth(coze_api_token), base_url=coze_api_base)

# The return values of the streaming interface can be iterated immediately.
for event in coze.chat.stream(
        # id of bot
        bot_id='7494277340248211490',
        # id of user, Note: The user_id here is specified by the developer, for example, it can be the
        # business id in the developer system, and does not include the internal attributes of coze.
        user_id='7486377818558578726',
        # user input
        additional_messages=[Message.build_user_question_text("可用智能体列表：[“神秘侦探”，“疑似嫌犯”，“知情目击者”]")]
        # conversation id, for Chaining conversation context
        # conversation_id='<conversation_id>',
):
    if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
        print(event.message.content, end="")

    if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
        print()
        # print("token usage:", event.chat.usage.token_count)