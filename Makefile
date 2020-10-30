all: install front mm
all_prod: install_prod front_prod mm
mm: makemigrations migrate
front: build collect
front_prod: build_prod collect
install: pip_install_upgrade npm_install
install_prod: pip_install_upgrade_prod npm_install

build:
	yarn --cwd l2-frontend build

build_prod:
	yarn --cwd l2-frontend build_prod

collect:
	python3 manage.py collectstatic --no-input

makemigrations:
	python3 manage.py makemigrations

migrate:
	python3 manage.py migrate

up:
	/bin/bash update-version.sh

npm_install:
	yarn --cwd l2-frontend

pip_install_upgrade:
	pip3 install --upgrade -r requirements.txt

pip_install_upgrade_prod:
	sudo -H pip3 install --upgrade -r requirements.txt

