PLUGIN_NAME := modular_units
DIST_DIR := dist
ZIP_FILE := $(DIST_DIR)/$(PLUGIN_NAME).zip

.PHONY: zip clean

zip:
	@mkdir -p $(DIST_DIR)
	@rm -f $(ZIP_FILE)
	@zip -r $(ZIP_FILE) $(PLUGIN_NAME) \
		-x "**/.DS_Store" \
		-x "**/__pycache__/**" \
		-x "**/*.pyc" \
		-x "**/.git/**" \
		-x "**/.gitignore" \
		-x "**/.env" \
		-x "**/.env.*" \
		-x "**/*.key" \
		-x "**/*.pem" \
		-x "**/*secret*" \
		-x "**/*credential*" \
		-x "**/*token*"

clean:
	@rm -rf $(DIST_DIR)
