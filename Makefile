PLUGIN_NAME := modular_units
DIST_DIR := dist
ZIP_FILE := $(DIST_DIR)/$(PLUGIN_NAME).zip
VERSION_FILE := $(PLUGIN_NAME)/__init__.py
BLENDER_VERSION ?= 5.0
BLENDER_ADDONS_DIR := $(HOME)/Library/Application Support/Blender/$(BLENDER_VERSION)/scripts/addons
BLENDER_BIN ?= /Applications/Blender.app/Contents/MacOS/Blender

.PHONY: zip bump-patch install clean-install clean

zip: bump-patch
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

bump-patch:
	@python3 scripts/bump_version.py $(VERSION_FILE)

clean:
	@rm -rf $(DIST_DIR)

install: zip
	@mkdir -p "$(BLENDER_ADDONS_DIR)"
	@unzip -o "$(ZIP_FILE)" -d "$(BLENDER_ADDONS_DIR)"
	@"$(BLENDER_BIN)" --background --python-expr "import bpy; bpy.ops.preferences.addon_enable(module='$(PLUGIN_NAME)'); bpy.ops.wm.save_userpref()"

clean-install: zip
	@mkdir -p "$(BLENDER_ADDONS_DIR)"
	@rm -rf "$(BLENDER_ADDONS_DIR)/$(PLUGIN_NAME)"
	@unzip -o "$(ZIP_FILE)" -d "$(BLENDER_ADDONS_DIR)"
	@"$(BLENDER_BIN)" --background --python-expr "import bpy; bpy.ops.preferences.addon_enable(module='$(PLUGIN_NAME)'); bpy.ops.wm.save_userpref()"
