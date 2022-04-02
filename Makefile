.PHONY: all zip clean format check install
all: zip

PACKAGE_NAME := control_playback

zip: $(PACKAGE_NAME).ankiaddon

$(PACKAGE_NAME).ankiaddon: src/*
	rm -f $@
	rm -rf src/__pycache__
	( cd src/; zip -r ../$@ * )

# Install in test profile
install:
	rm -rf src/__pycache__
	rm -rf ankiprofile/addons21/$(PACKAGE_NAME)
	cp -r src/. ankiprofile/addons21/$(PACKAGE_NAME)

format:
	python -m black src/

check:
	python -m mypy src/

clean:
	rm -f $(PACKAGE_NAME).ankiaddon
