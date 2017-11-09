DASH = va_dashboard
.PHONY: all

all: $(DASH)/node_modules $(DASH)/static/bundle.js

$(DASH)/node_modules: $(DASH)/package.json
	cd $(DASH) && npm install

$(DASH)/static/bundle.js: $(DASH)/node_modules $(DASH)/src/*.js 
	cd $(DASH) && npm run build
