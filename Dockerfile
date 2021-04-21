FROM python:3 #base image over which current application is built
WORKDIR /usr/src/app #sets the working directory path for the further commands
COPY requirements.txt . 
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . . #copies the contents from current folder to current working directory set above
ENTRYPOINT [ "python" ]
CMD [ "app.py" ]
