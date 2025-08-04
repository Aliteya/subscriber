FROM public.ecr.aws/lambda/python:3.12

WORKDIR /app

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app .

CMD [ "main.lambda_handler" ]