FROM python:3
RUN apt-get update && apt-get -y install cmake protobuf-compiler
LABEL Author="Kevin"
LABEL E-mail="kevin@appmartgroup.com"

COPY . /facial
WORKDIR /facial
RUN pip install -r requirements.txt
CMD [ "python", "run.py" ]