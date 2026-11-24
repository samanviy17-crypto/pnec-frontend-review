
.PHONY: install serve build clean

# Install the project's dependencies
install:
	bundle install

# Run the website locally
serve:
	bundle exec jekyll serve

# Build the website
build:
	bundle exec jekyll build

# Remove generated website files
clean:
	bundle exec jekyll clean
