#install:
#	#install commands
#	pip install --upgrade pip &&\
#		pip install -r requirements.txt
#format:
#	#format commands
#	black *.py mylib/*.py
#lint:
#	#flake8 or pylint commands
#	pylint --disable=R,C *.py mylib/*.py
#test:
#	#test commands
#	python -m pytest -vv --cov=mylib --cov=main test_*.py
#build:
#	#build container
#	docker build -t deploy-fastapi .
#run:
#	#run container
#	#docker run -p 8080:8080 28dfb1edb760
#deploy:
#	#deploy commands
#	#aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 590183839343.dkr.ecr.us-east-1.amazonaws.com
#	#docker build -t icon-product-api .
#	#docker tag icon-product-api:latest 590183839343.dkr.ecr.us-east-1.amazonaws.com/icon-product-api:latest
#	#docker push 590183839343.dkr.ecr.us-east-1.amazonaws.com/icon-product-api:latest
#
#all: install lint test build
install:
	pip install --upgrade pip && pip install -r requirements.txt

format:
	black *.py mylib/*.py

lint:
	pylint --disable=R,C *.py mylib/*.py

test:
	python -m pytest -vv --cov=mylib --cov=main test_*.py

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

all: install lint test build
