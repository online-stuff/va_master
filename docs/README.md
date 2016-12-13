## Basics

When you install the master, the following is deployed:

* supervisord (a process control system that manages the whole master)
   * This allows us to run on any init system

* Salt Master
   * Used for deploying and managing instances

* Dashboard
   * Control the master, all apps are specified and ran from here.

* Dashboard + REST API
   * Everything is controlled by the dashboard. The API powers the dashboard and mobile app and handles authentication, scheduling tasks, communication with Salt, Consul and scheduler

* Scheduler
   * Checks apps by talking with Consul, runs apps by talking with Salt.

* Consul
   * A monitoring service and a key-value store.

## How the dashboard frontend works
The web frontend is a single-page JavaScript. The whole bundle is compiled by running `nodejs ./dashboard/bundle.js`. We are using React+Redux to render the page and manage the state.

All communication is done via the REST API.

## How the REST API works

The REST API is a Python app that is based on Tornado async web framework.

## Useful reads

* Frontend
   * https://facebook.github.io/react/
   * http://redux.js.org/docs/basics/

* API
   * http://www.tornadoweb.org/en/stable/guide.html

* Scheduler
   * https://docs.saltstack.com/en/develop/ref/clients/index.html
