install:
	#install commands
	pip install --upgrade pip &&\
		pip install -r requirements.txt
format:
	#format commands
	black *.py mylib/*.py
lint:
	#flake8 or pylint commands
	pylint --disable=R,C *.py mylib/*.py
test:
	#test commands
	python -m pytest -vv --cov=mylib --cov=main test_*.py
build:
	#build container
	docker build -t deploy-fastapi .
run:
	#run container
	#docker run -p 8080:8080 28dfb1edb760
deploy:
	#deploy commands
all: install lint test build run deploy