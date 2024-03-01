FROM ghcr.io/osgeo/gdal:alpine-normal-3.8.4

# Set the working directory in the container
WORKDIR /alti3d-dl

# Install Python and pip
RUN apk add --no-cache python3 py3-pip
RUN echo "alias python=python3" >> ~/.bashrc

# Copy the current directory contents into the container at /downloader
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run the script when the container launches
CMD ["python", "download_manager.py"]
