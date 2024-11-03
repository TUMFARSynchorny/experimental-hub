# SynthARium

An online tool for researchers to host and conduct customizable online experiments with users.

![Quick Demo Exp Hub](https://raw.githubusercontent.com/wiki/TUMFARSynchrony/experimental-hub/images/exp-quick-demo-small.gif)

As a part of our vision for SynthARium (formerly experimental-hub), we hope to make at-home video conferencing studies have more laboratory control through the **experimenter and participant workflows** we have designed to allow safeguards in the workflow and a flexible UI (e.g. custom participant video screen position, size, and order, limiting participant exposure pre-experiment to others in the call or seeing themselves with a filter too early, etc.). We also hope that the [experimental templates](https://github.com/TUMFARSynchrony/experimental-hub/tree/ce-documentation/backend/sessions) and [filters](https://github.com/TUMFARSynchrony/experimental-hub/tree/ce-documentation/backend/filters) our platform uses helps the **egological validity and repeatability** of both HCI and psychology experiments and encourages sharing of anonymized data of the experiment. Finally, because our experimental hub is self-hosted, there should be more control over the **data privacy** of where potentially sensitive video and audio data is being stored.

For detailed motivation about SynthARium see our [introduction to the Experimental Hub](https://github.com/TUMFARSynchrony/experimental-hub/wiki/), read our [UbiComp'23 poster paper](https://dl.acm.org/doi/abs/10.1145/3594739.3610686), or checkout our [Medium blog](https://medium.com/ubicomp-iswc-2023/an-experimental-video-conferencing-platform-to-bridge-the-gap-in-communication-1b84f2a3b954). Otherwise, get started with our [quick start](./README.md#Building&Starting) or [detailed set up instructions](https://github.com/TUMFARSynchrony/experimental-hub/wiki/Project-Setup) to try it out yourself!

# Setup

<!-- **TODO**: _pre-build release can be found_ ...

**TODO**: _quick setup / start + requirements_
--- -->

## Building & Quick Starting Guide

In case you want to build the frontend yourself, follow the steps in this section.

For the general setup and prerequisites, please take a look at the [frontend](./frontend/README.md#configuration) and [backend](./backend/README.md#configuration) READMEs.
Continue with the steps bellow after both the frontend and backend are set up.

1. Build frontend
   - Skip this step if there were no changes to the frontend since the last build process
   - Go to the frontend directory: `cd frontend`
   - If this is your first time running the experimental hub run: `npm install`
   - Build the frontend: `npm run build`. Make sure the build process finishes without any errors
2. (Re-) Start server
   - If the server is already running: stop the server
   - Make sure to take a look at the settings. For more details see [backend configuration](./backend/README.md#configuration)
     - It is recommended to set `environment` to `prod` to disable [CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
   - In your venv, run `pip install -r requirements.txt` [(click here for more detailed instructions on setting up a virtual environment)](https://github.com/TUMFARSynchrony/experimental-hub/wiki/Project-Setup#creating-a-virtual-environment)
   - Start the server by executing `main.py` in the backend directory. For example from the root directory: `python backend/main.py`
3. In your favorite browser (tested mainly with Chrome) go to [http://localhost:8080/](http://localhost:8080/) or [https://localhost:8080/](https://localhost:8080/) depending on your projects configuration.

### Notes

- For development, the React / frontend development server is recommended: `npm start`
