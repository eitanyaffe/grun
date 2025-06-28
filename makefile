include config.mk
include rules.mk

#####################################################################################
# print variable value
#####################################################################################

# print the value of any makefile variable
print-%:
	@echo $($*)

#####################################################################################
# Installation
#####################################################################################

# Installs the evo_gcp script to a system-wide directory.
# This may require superuser privileges (e.g., 'sudo make install').
INSTALL_DIR ?= /usr/local/bin
INSTALL_NAME = evo_gcp

.PHONY: install uninstall

install:
	@mkdir -p $(INSTALL_DIR)
	@install -m 755 evo_gcp.py $(INSTALL_DIR)/$(INSTALL_NAME)
	@echo "✅ $(INSTALL_NAME) installed to $(INSTALL_DIR)"
	@echo "\nMake sure '$(INSTALL_DIR)' is in your PATH."

uninstall:
	@rm -f $(INSTALL_DIR)/$(INSTALL_NAME)
	@echo "🗑️ Uninstalled $(INSTALL_NAME) from $(INSTALL_DIR)"
