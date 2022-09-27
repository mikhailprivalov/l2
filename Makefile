all: install front mm
all_prod: install_prod front_prod mm
mm: makemigrations migrate
front: build collect
front_prod: build_prod collect
install: poetry_bootstrap npm_install
install_prod: poetry_bootstrap npm_install
release: update_browserlist up git_commit_up git_push
version_updater: update_browserlist up

watch:
	yarn --cwd l2-frontend serve

update_browserlist:
	-(cd l2-frontend && npx --yes browserslist@latest --update-db && cd ..)

build:
	yarn --cwd l2-frontend build

build_prod:
	yarn --cwd l2-frontend build_prod

ci_lint:
	yarn --cwd l2-frontend ci:lint

collect:
	python manage.py collectstatic --no-input

makemigrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

up:
	/bin/bash update-version.sh

npm_install:
	yarn --cwd l2-frontend

npm_install_cached:
	yarn --prefer-offline --cwd l2-frontend

poetry_bootstrap:
	poetry install

git_commit_up:
	git commit -a -m "Up version"

git_push:
	git push
