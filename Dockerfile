# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Using --no-cache-dir to keep the image size small
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's source code from your host to your image filesystem.
COPY . .

# Set the PYTHONPATH to the root of the app so imports work correctly
ENV PYTHONPATH="/app"

# Define the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define the command to run your app using uvicorn
# The --host 0.0.0.0 makes the server accessible from outside the container
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
