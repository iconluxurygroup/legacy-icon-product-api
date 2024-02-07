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
	python -m pytest -vv --cov=mylib test_logic.py
build:
	#build container
deploy:
	#deploy commands
all: install lint test deploy