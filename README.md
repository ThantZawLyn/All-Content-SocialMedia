# Create Dockerfile.base

#Use an official Python runtime as a parent image
FROM joyzoursky/python-chromedriver:3.8-selenium

#Set the working directory in the container
WORKDIR /app

#Copy the requirements file into the container
COPY requirements.txt .

#Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

#Copy your Python project files into the container
COPY app.py .

#Define the command to run your Python application
CMD ["python", "app.py"]

# Docker build command line
1) $docker build -t my-python-base-image:1.3 -f Dockerfile.base .
2) $ docker login
3) $ docker tag my-python-base-image:1.3 mglue/my-python-base-image:1.3
4) $ docker push mglue/my-python-base-image:1.3
   
# Create Dockerfile.app
#Use your custom base image as the base image
FROM mglue/my-python-base-image:1.3

#Set the working directory in the container
WORKDIR /app

#Copy the requirements file into the container
COPY keyword.txt .

#Copy the requirements.txt file into the container
COPY stopword.txt .

#Copy your Python project files into the container
COPY app.py .

#Run the NLP application
CMD ["python", "app.py"]

# Command line
1) $ docker build -t my-python-app:1.0 -f Dockerfile.app .
2) $ docker login
3) $ docker tag my-python-app:1.0 mglue/my-python-app:1.0
4) $ docker push mglue/my-python-app:1.0
5) 
# Push Code to GitHub
1) git add . 
2) git commit -m "Initial commit"
3) git remote add origin https://github.com/ThantZawLyn/Yae-Naung-App.git
4) git branch -M main
5) git push -u origin main
# Set Up GitHub Actions for Continuous Integration (CI)
Create a .github/workflows/docker.yml file in GitHub repository 
# Set Up Docker Hub and Push Docker Image
docker login -u username -p yourpassword
# Deploy Application on Kubernetes
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
