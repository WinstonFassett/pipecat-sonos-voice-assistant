# Pipecat Sonos Voice Assistant

A voice assistant that can control Sonos speakers via natural language using the Pipecat framework and Model Context Protocol (MCP).

## Features

- Control Sonos speakers using natural language voice commands
- WebRTC-based interface for voice interaction
- Uses Deepgram for Speech-to-Text
- Uses Cartesia for Text-to-Speech
- Uses OpenAI for natural language understanding
- Connects to Sonos speakers via MCP
- Docker support for easy deployment

## Requirements

- Python 3.12+
- Sonos speakers on your network
- API keys for:
  - Deepgram (Speech-to-Text)
  - Cartesia (Text-to-Speech)
  - OpenAI (LLM)

## Installation

### Standard Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/pipecat-sonos-voice-assistant.git
cd pipecat-sonos-voice-assistant
```

2. Install dependencies:
```bash
pip install -e .
```

3. Copy `.env.example` to `.env` and add your API keys:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

The application uses `mcp_registry_config.json` to configure MCP servers. The file should contain:

```json
{
  "mcpServers": {
    "sonos": {
      "command": "sonos-mcp-server",
      "args": [],
      "env": {},
      "description": "Sonos MCP Server for controlling Sonos speakers"
    }
  }
}
```

### Environment Variables

Copy `.env.example` to create your own `.env` file with the following variables:

- `DEEPGRAM_API_KEY`: Your Deepgram API key for speech recognition
- `CARTESIA_API_KEY`: Your Cartesia API key for text-to-speech
- `OPENAI_API_KEY`: Your OpenAI API key for language processing
- `OPENAI_MODEL`: The OpenAI model to use (default: gpt-4o-mini)
- `CARTESIA_VOICE_ID`: The voice ID to use for text-to-speech
- `HOST`: Host to bind the server to (default: localhost)
- `PORT`: Port to run the server on (default: 7860)

## Usage

### Running Locally

```bash
python server.py
```

The application will start a web server at http://localhost:7860. Open this URL in a browser to interact with the voice assistant.


## How it Works

1. The application starts a WebRTC server using Pipecat
2. User voice input is captured through the browser
3. Deepgram converts speech to text
4. OpenAI processes the text to understand commands
5. The MCP system executes commands on Sonos speakers
6. Cartesia converts response text back to speech
7. The audio response is sent back to the user

## Project Structure

- `server.py`: Main application entry point
- `run.py`: WebRTC server setup
- `mcp_registry.py`: Registry for MCP servers
- `mcp_registry_config.json`: Configuration for MCP servers
- `pyproject.toml`: Project dependencies and metadata
- `.env.example`: Example environment variable configuration
