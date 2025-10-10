# Makefile for auto testing

# ***************************************************************************************
#    CONFIGURATION section
# ***************************************************************************************
# don't delete network after testing
# TEST_ARG             := --no-delete
# Path for each test cases
REGISTER        := $(CURDIR)/Testset/Register

# ***************************************************************************************
#    Test section
# ***************************************************************************************
all: register

.PHONY: register
register:
	python3 -m sipssert '$(REGISTER)'