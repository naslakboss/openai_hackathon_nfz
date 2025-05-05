# NFZ Twilio Bot

A Twilio-based chatbot for NFZ (National Health Fund) services, built with Python and OpenAI.

## Overview

This project implements a Twilio-based chatbot that helps users interact with NFZ services through SMS. It uses OpenAI's language models for natural language processing and Twilio for SMS communication.

## Features

- SMS-based interaction with NFZ services
- Natural language processing using OpenAI
- FastAPI backend for handling Twilio webhooks
- Docker support for easy deployment
- Environment-based configuration

## Prerequisites

- Python 3.10+
- Linux, MacOS, or Windows Subsystem for Linux (WSL)
- [Docker](https://www.docker.com) (optional, for containerized deployment)
- Twilio Account and API credentials
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd twilio-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your API keys and configuration
```

## Configuration

Create a `.env` file with the following variables:
```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
OPENAI_API_KEY=your_openai_api_key
```

## Usage

1. Start the server:
```bash
python server.py
```

2. Configure your Twilio webhook to point to your server's endpoint:
```
https://your-domain.com/webhook
```

## Development

The project structure is organized as follows:
- `server.py` - FastAPI server and webhook handler
- `bot.py` - Core bot logic and message processing
- `nfz_api.py` - NFZ API integration
- `twilio_sms.py` - Twilio SMS handling
- `templates/` - Message templates
- `bot_types.py` - Type definitions

## Dependencies

This project uses several key dependencies:
- FastAPI for the web server
- Twilio for SMS communication
- OpenAI for natural language processing
- LangChain for AI agent functionality
- Python-dotenv for environment management

For a complete list of dependencies, see `requirements.txt`.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Twilio](https://www.twilio.com) for SMS communication
- [OpenAI](https://openai.com) for language models
- [FastAPI](https://fastapi.tiangolo.com) for the web framework
- [LangChain](https://www.langchain.com) for AI agent framework

## Support

For support, please open an issue in the repository or contact the maintainers.
