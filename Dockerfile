# Use Python 3.11 slim image as base
FROM python:3.11
# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a non-root user
# RUN useradd -m botuser && chown -R botuser:botuser /app
# USER botuser

# Command to run the bot
CMD ["python", "-m", "taskmanager"] 