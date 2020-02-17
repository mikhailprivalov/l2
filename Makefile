all: front mm
all_prod: front_prod mm
mm: makemigrations migrate
front: build collect
front_prod: build_prod collect

build:
	npm run --prefix l2-frontend build

build_prod:
	npm run --prefix l2-frontend build_prod

collect:
	python3 manage.py collectstatic --no-input

makemigrations:
	python3 manage.py makemigrations

migrate:
	python3 manage.py migrate

up:
	/bin/bash update-version.sh
