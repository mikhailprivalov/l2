all: install front mm
all_prod: install_prod front_prod mm
all_fast: poetry_bootstrap front_fast mm_fast
mm: makemigrations migrate
mm_fast: makemigrations_fast migrate_fast
front: build collect
front_prod: build_prod collect
front_fast: take_release collect_fast
install: poetry_bootstrap npm_install
install_prod: poetry_bootstrap npm_install
release: update_browserlist up git_commit_up git_push
version_updater: update_browserlist up
fast: checkout_last all_fast

watch:
	yarn --cwd l2-frontend serve

update_browserlist:
	-(cd l2-frontend && npx --yes browserslist@latest --update-db && cd ..)

build:
	yarn --cwd l2-frontend build
	-rm -rf static/webpack_bundles

build_prod:
	yarn --cwd l2-frontend build_prod

ci_lint:
	yarn --cwd l2-frontend ci:lint

collect:
	python manage.py collectstatic --no-input

collect_fast:
	poetry run python manage.py collectstatic --no-input

makemigrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

migrate_fast:
	poetry run python manage.py migrate

makemigrations_fast:
	poetry run python manage.py makemigrations

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

take_release:
	poetry run python take_release.py

checkout_last:
	/bin/bash checkout_last.sh
