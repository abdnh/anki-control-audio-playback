.PHONY: all zip clean fix mypy install
all: zip

PACKAGE_NAME := control_playback

zip: $(PACKAGE_NAME).ankiaddon

SRC := $(wildcard src/**)

$(PACKAGE_NAME).ankiaddon: $(SRC)
	rm -f $@
	rm -rf src/__pycache__
	( cd src/; zip -r ../$@ * )

# Install in test profile
ankiprofile/addons21/$(PACKAGE_NAME): $(SRC)
	rm -rf src/__pycache__
	cp -r src/. ankiprofile/addons21/$(PACKAGE_NAME)

install: ankiprofile/addons21/$(PACKAGE_NAME)

fix:
	python -m black src
	python -m isort src

mypy:
	python -m mypy src --disallow-untyped-defs

pylint:
	python -m pylint src

clean:
	rm -f $(PACKAGE_NAME).ankiaddon
