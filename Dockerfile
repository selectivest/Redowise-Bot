# Use Python 3.11 slim image as base
FROM python:3.12
# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    gfortran \
    libatlas-base-dev \
    libblas-dev \
    liblapack-dev \
    libffi-dev \
    python3-dev \
    pkg-config \
    cmake \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*


# Copy the rest of the application
COPY . .
RUN pip3 install .
RUN pip3 install -r requirements.txt

# Create a non-root user
# RUN useradd -m botuser && chown -R botuser:botuser /app
# USER botuser
# Command to run the bot
CMD ["python",  "taskmanager/bot.py"] 
#CMD ["tail", "-f", "/dev/null"] 