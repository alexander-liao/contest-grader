# Use an official Fedora runtime as a parent image
FROM fedora:26

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN dnf install -y python-pip
RUN pip3 install --user --trusted-host pypi.python.org -r requirements.txt
RUN dnf install -y java
RUN dnf install -y java-1.8.0-openjdk
RUN dnf install -y java-1.8.0-openjdk-devel
RUN dnf install -y gcc-c++
RUN dnf install -y ruby

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["python3", "grader.py"]
