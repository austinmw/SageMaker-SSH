SHELL := /bin/bash

synth-deploy: synth deploy
	. .venv/bin/activate && \
	python obtain_key.py get

install:
	. .venv/bin/activate && \
	pip install -r requirements.txt -q

bootstrap: install
	. .venv/bin/activate && \
	cdk bootstrap

synth: install
	. .venv/bin/activate && \
	cdk synth

deploy: install
	. .venv/bin/activate && \
	cdk deploy --all --require-approval never --outputs-file outputs.json

key: install
	. .venv/bin/activate && \
	python obtain_key.py get

destroy: install
	. .venv/bin/activate && \
	cdk destroy --all

clean: install
	. .venv/bin/activate && \
	cdk destroy --all --force && \
	python obtain_key.py remove
	rm -rf cdk.out
	rm outputs.json
