# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for compiling Python packages and running OpenCV
RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    libglib2.0-0 \ 
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && apt-get clean \ 
    && rm -rf /var/lib/apt/lists/* 

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files to the working directory
COPY . .

# Set the command to run your application
CMD ["python", "GuardianViewSystem.py"]
