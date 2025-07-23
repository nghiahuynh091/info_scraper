# OptiBot Dockerfile - Both Node.js and Python

FROM node:18-slim


RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


COPY package*.json ./
RUN npm install

COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY main.py ./
COPY optibot.py ./
COPY config.py ./
COPY src/ ./src/

RUN mkdir -p articles reports

CMD ["python3", "main.py"]
