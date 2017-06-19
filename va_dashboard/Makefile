source_files := $(wildcard *.js)
.PHONY: all

all: node_modules static/bundle.js

node_modules: package.json
	npm install

static/bundle.js: node_modules src/*.js 
	npm run build
