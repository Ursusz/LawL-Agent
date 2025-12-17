# Start with a modern Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install uv - a fast Python package installer
RUN pip install uv

# Copy the requirements file into the container
COPY requirements.lock .

# Create the virtual environment
# The venv will be created at /app/lawl
RUN uv venv lawl

# Install the Python dependencies into the virtual environment
# using the -p flag to specify the Python interpreter of the venv.
RUN uv pip install -p /app/lawl/bin/python -r requirements.lock

# Copy the rest of the backend source code into the container
COPY ./src ./src

# The credentials.json file needs to be present in the build context
# and will be copied into the correct location inside the image.
COPY ./src/utilities/service_account_key.json ./src/utilities/service_account_key.json

# Expose the port the server will run on
EXPOSE 8000

# Command to run the uvicorn server using the venv's Python interpreter.
# This is the most reliable way to ensure the correct dependencies are used.
# Note: --host 0.0.0.0 is crucial to make the server accessible from outside the container
CMD ["/app/lawl/bin/python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
