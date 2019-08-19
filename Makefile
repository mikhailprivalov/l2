all: build collect
all_prod: build_prod collect

build:
	npm run --prefix l2-frontend build

build_prod:
	npm run --prefix l2-frontend build_prod

collect:
	python3 manage.py collectstatic --no-input
