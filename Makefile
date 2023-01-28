all: deprecation_make_all_warning continue_confirmation install front mm
all_poetry: install_prod front_poetry mm_poetry
all_prod: deprecation_make_all_prod_warning continue_confirmation install_prod front_prod mm
all_fast: poetry_bootstrap front_fast mm_poetry
postinstall: collect_poetry mm_poetry
postinstall_with_build_front: npm_install front_poetry mm_poetry
mm: makemigrations migrate
mm_poetry: makemigrations_poetry migrate_poetry
front: build collect
front_poetry: build collect_poetry
front_prod: build_prod collect
front_fast: take_release collect_poetry
install: poetry_bootstrap npm_install
install_prod: poetry_bootstrap npm_install
release: update_browserlist up git_commit_up git_push
version_updater: update_browserlist up
fast: checkout_last all_fast
l2_setup: poetry_bootstrap l2_run_setup

l2_run_setup:
	@poetry run python setup.py

deprecation_make_all_warning:
	@echo "\033[1mmake all is deprecated, use make all_poetry instead for development purposes\033[0m"

deprecation_make_all_prod_warning:
	@echo "\033[1mmake all_prod is deprecated, use make all_fast instead for production purposes\033[0m"

continue_confirmation:
	@echo "Are you sure you want to continue? [y/N]"
	@read ans; if [ "$$ans" != "y" ]; then exit 1; fi

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

collect_poetry:
	poetry run python manage.py collectstatic --no-input

makemigrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

migrate_poetry:
	poetry run python manage.py migrate

makemigrations_poetry:
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
