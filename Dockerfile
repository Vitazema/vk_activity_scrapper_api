FROM python:3
WORKDIR /vk_spider_api
COPY requirements.txt /vk_spider_api
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
COPY . .