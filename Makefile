all: build collect

build:
	npm run --prefix l2-frontend build

collect:
	python3 manage.py collectstatic --no-input
