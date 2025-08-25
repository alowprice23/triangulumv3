#!/bin/sh
#
# This is a simple entrypoint script for the Docker container.
# It executes any command passed to it.
# This allows the Docker image to be flexible and run different commands,
# such as starting the web server or running the CLI.

# The `exec` command replaces the shell process with the command,
# which is good practice for entrypoint scripts.
exec "$@"
