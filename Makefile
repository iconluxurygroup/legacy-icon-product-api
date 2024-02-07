install:
	#install commands
	pip install --upgrade pip &&\
		pip install -r requirements.txt
lint:
	#flake8 or pylint commands
test:
	#test commands
deploy:
	#deploy commands
all: install lint test deploy