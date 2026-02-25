# UAV Log Viewer

![log seeking](preview.gif "Logo Title Text 1")

This is a Javascript based log viewer for Mavlink telemetry and dataflash logs.
[Live demo here](http://plot.ardupilot.org).

## Chatbot Feature — Agent Building Focus

This fork adds an **agentic chatbot** for MAVLink flight log analysis. The implementation emphasizes **Agent Building**: following agentic standards and use of state-of-the-art tools.

**Highlights:**
- **Conversation state** — Multi-turn dialog with persistent context
- **Proactive clarification** — Asks for more info when data is insufficient
- **Dynamic data retrieval** — Infers message types from natural language
- **Flexible reasoning** — LLM reasons over telemetry + anomaly hints (no hardcoded rules)
- **Multi-provider** — OpenAI or Anthropic via `LLM_PROVIDER`

See **[AGENT_BUILDING.md](AGENT_BUILDING.md)** for design details. Quick start: [CHATBOT_FEATURE.md](CHATBOT_FEATURE.md).

**Run the chatbot:**
```bash
pip install -r requirements.txt
uvicorn backend.presentation.api.main:app --reload
# Open http://127.0.0.1:8000/ui
```

## Build Setup

``` bash
# initialize submodules
git submodule update --init --recursive

# install dependencies
npm install

# enter Cesium token
export VUE_APP_CESIUM_TOKEN=<your token>

# serve with hot reload at localhost:8080
npm run dev

# build for production with minification
npm run build

# run unit tests
npm run unit

# run e2e tests
npm run e2e

# run all tests
npm test
```

# Docker

run the prebuilt docker image:

``` bash
docker run -p 8080:8080 -d ghcr.io/ardupilot/uavlogviewer:latest

```

or build the docker file locally:

``` bash

# Build Docker Image
docker build -t <your username>/uavlogviewer .

# Run Docker Image
docker run -e VUE_APP_CESIUM_TOKEN=<Your cesium ion token> -it -p 8080:8080 -v ${PWD}:/usr/src/app <your username>/uavlogviewer

# Navigate to localhost:8080 in your web browser

# changes should automatically be applied to the viewer

```
