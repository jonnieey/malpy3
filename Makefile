BUILD_FILES = build/ dist/
DOC_BUILD_FILES = docs/build

help:
	@echo "make setup"
	@echo "	Create development environment"
	@echo 
	@echo "make install"
	@echo "	Install root package"
	@echo 
	@echo "make clean"
	@echo "	Clean build,tmp files"
	@echo 
	@echo "make format"
	@echo "	Format code"
	@echo 


setup:
	poetry install --no-root

install:
	poetry install --no-dev

clean:
	find . -name __pycache__ -name *.pyc | xargs rm -rfv;
	rm -rfv $(BUILD_FILES)

format:
	black mal tests

