FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy application code
COPY . .

# Install dependencies
RUN uv venv
RUN uv sync

# Run the bot
CMD ["uv", "run", "main.py"]
