SHELL := /bin/bash

.PHONY: dev start local stop kill clean-ports

dev: start

local: start

start:
	@./scripts/start-local.sh

stop:
	@./scripts/stop-local.sh

kill: stop

clean-ports: stop
