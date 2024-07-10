#!/bin/sh
# This is a simple script that will keep the service running if no command is provided
# It will exit when a SIGTERM is received
# You can connect via `docker exec -it name_of_container bash` and test your environment

set -e

exit_backend() {
  echo "Exiting backend"
  exit 0
}

trap exit_backend INT TERM

# Hang out until SIGTERM received
while true; do
    sleep 1
done