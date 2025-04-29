# Multi-Agent Chat Group with Coze

A Flask-based web application for interacting with multiple Agents on the Coze platform.

## Features

- Multi-agent support with the ability to choose different agents for conversation
- Intelligent selection feature that automatically assigns the most suitable agent based on the question
- Independent conversation context maintenance for each agent
- Real-time response display
- Clean and beautiful interface design
- Support for resetting specific agent or all conversation history

## Project Structure

```
├── app.py           # Main application and routes
├── config.py        # Configuration file (agents and API settings)
├── dispatcher.py    # Dispatch-related logic
├── requirements.txt # Dependencies
├── static/          # Static resources
└── templates/       # HTML templates
    └── index.html   # Main page template
```

## Installation

1. Clone or download this repository

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Set environment variables (optional)

If you need to use a non-default Coze API address, create a `.env` file and set:

```
COZE_API_BASE=your_api_address
```

## Running the Application

```bash
python app.py
```

The application will run locally, accessible at http://127.0.0.1:5000/

## Customization

In the `config.py` file, you can modify the following parameters:

- `COZE_API_TOKEN`: Your Coze API token
- `AVAILABLE_AGENTS`: Define the list of available agents, including ID, name, and description
  
```python
AVAILABLE_AGENTS = [
    {
        "id": "Your Bot ID",
        "name": "Agent Name",
        "description": "Agent Description"
    },
    # Add more agents...
]
```

- `DISPATCHER_AGENT`: Configuration for the dispatcher agent

```python
DISPATCHER_AGENT = {
    "id": "Your Dispatcher Bot ID",
    "name": "Intelligent Dispatcher",
    "description": "Selects the appropriate agent based on user questions"
}
```

## Extending Dispatch Logic

To customize or extend the dispatch logic, modify the relevant functions in `dispatcher.py`:

- `build_dispatch_prompt`: Define the prompt sent to the dispatcher
- `extract_agent_from_response`: Extract agent information from dispatcher response
- `extract_analysis`: Extract and format dispatch analysis results
- `process_dispatch`: Overall dispatch processing flow

## Usage

The application supports two conversation modes:

### Manual Selection Mode
1. Select the agent to chat with from the dropdown menu at the top of the interface
2. Enter your question in the input box and click send
3. To reset the conversation history for the current agent, click the "Reset Conversation" button

### Intelligent Selection Mode
1. Click the "Intelligent Selection" switch at the top of the interface to enable the feature
2. Enter any question in the input box
3. The system will automatically call the dispatcher agent to analyze your question
4. The dispatcher will select the most suitable agent to answer your question
5. The selected agent will automatically respond to your question
6. The intelligent selection results will be displayed above the conversation

## Notes

- This application uses sessions to maintain conversation context, please ensure your browser allows cookies
- Each agent's conversation context is independent
- In intelligent selection mode, you can reset all agents' conversation history with one click
- For production deployment, please set a more secure `SESSION_SECRET` in config.py 