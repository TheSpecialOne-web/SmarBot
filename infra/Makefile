.PHONY: deploy-scripts
deploy-scripts:
	cd scripts/$(SCRIPT_NAME) && \
	az acr build --registry $(ACR_NAME) --image $(SCRIPT_NAME):latest --file Dockerfile .
