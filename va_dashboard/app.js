var React = require('react');
var ReactDOM = require('react-dom');
var Router = require('react-router');
var Redux = require('redux');
var ReactRedux = require('react-redux');
var Network = require('./network');

var connect = ReactRedux.connect;
var Provider = ReactRedux.Provider;

function auth(state, action){
    if(typeof state === 'undefined'){
        var storageState = window.localStorage.getItem('auth'); // Check session
        if(storageState !== null) {
            return JSON.parse(storageState);
        } else {
            return {token: null, username: null, loginError: false, inProgress: false};
        }
    }

    var newState = Object.assign({}, state);
    if(action.type == 'LOGIN_START' || action.type === 'LOGOUT' || action.type == 'LOGIN_ERROR'){
        newState.username = null;
        newState.token = null;
        newState.loginError = false;
        newState.inProgress = false;
    }
    if(action.type === 'LOGIN_START') newState.inProgress = true;
    if(action.type === 'LOGIN_ERROR') newState.loginError = true;
    if(action.type === 'LOGIN_GOOD') {
        newState.username = action.username;
        newState.token = action.token;
        newState.loginError = false;
        newState.inProgress = false;
    }
    // Add into session
    window.localStorage.setItem('auth', JSON.stringify(newState));
    return newState;
};

function table(state, action){
    if(typeof state === 'undefined'){
        return {};
    }
    var newState = Object.assign({}, state);

    if(action.type == 'ADD_DATA'){
        newState = action.tables;
    }
    if(action.type == 'CHANGE_DATA'){
        newState[action.name] = action.data;
    }
    return newState;
}

function filter(state, action){
    if(typeof state === 'undefined'){
        return {filterBy: ""};
    }

    var newState = Object.assign({}, state); 
    if(action.type == 'FILTER'){
        newState.filterBy = action.filterBy;
    }
    if(action.type == 'RESET_FILTER'){
        newState.filterBy = "";
    }

    return newState;
};

function modal(state, action){
    if(typeof state === 'undefined'){
        return {isOpen: false, template: { title: "", content: [], buttons: [], args: []}};
    }

    var newState = Object.assign({}, state);
    if(action.type == 'OPEN_MODAL'){
        if("template" in action)
            newState.template = action.template;
        newState.isOpen = true;
    }
    if(action.type == 'CLOSE_MODAL'){
        newState.template = { title: "", content: [], buttons: [], args: []};
        newState.isOpen = false;
    }

    return newState;
};

function apps(state, action){
    if(typeof state === 'undefined'){
        return {select: ""};
    }

    var newState = Object.assign({}, state);
    if(action.type == 'LAUNCH'){
        newState.select = action.select;
    }
    if(action.type == 'RESET_APP'){
        newState.select = "";
    }

    return newState;
};

function div(state, action){
    if(typeof state === 'undefined'){
        return {show: 'hidden'};
    }

    var newState = Object.assign({}, state);
    if(action.type == 'TOGGLE'){
        newState.show = newState.show ? '':'hidden';
    }

    return newState;
};

function panel(state, action){
    if(typeof state === 'undefined'){
        return {panel: '', instance: ''};
    }

    var newState = Object.assign({}, state);
    if(action.type == 'CHANGE_PANEL'){
        newState.panel = action.panel;
        newState.instance = action.instance;
    }

    return newState;
};

function alert(state, action){
    if(typeof state === 'undefined'){
        return {msg: '', show: false};
    }

    var newState = Object.assign({}, state);
    if(action.type == 'SHOW_ALERT'){
        newState.msg = action.msg;
        newState.show = true;
    }
    if(action.type == 'HIDE_ALERT'){
        newState.msg = '';
        newState.show = false;
    }

    return newState;
};

function form(state, action){
    if(typeof state === 'undefined'){
        return {readonly: {}};
    }

    var newState = Object.assign({}, state);
    if(action.type == 'SET_READONLY'){
        newState.readonly = action.readonly;
    }
    if(action.type == 'RESET_FORM'){
        newState.readonly = {};
    }

    return newState;
};

var mainReducer = Redux.combineReducers({auth: auth, table: table, filter: filter, modal: modal, apps: apps, div: div, panel: panel, alert: alert, form: form});
var store = Redux.createStore(mainReducer);

var Home = require('./tabs/home');
var Overview = require('./tabs/overview');
var Hosts = require('./tabs/hosts');
var Apps = require('./tabs/apps');
var Store = require('./tabs/store');
var Panel = require('./tabs/panel');
var Subpanel = require('./tabs/subpanel');
var Vpn = require('./tabs/vpn');
var VpnLogins = require('./tabs/vpn_logins');
var ChartPanel = require('./tabs/chart_panel');
var Triggers = require('./tabs/triggers');
var Ts_status = require('./tabs/ts_status');

var Login = require('./login');
var App = React.createClass({
  render: function() {
    return (
        <Router.Router history={Router.hashHistory}>
            <Router.Route path='/' component={Home}>
                <Router.IndexRoute component={Overview} />
                <Router.Route path='/hosts' component={Hosts} />
                <Router.Route path='/apps' component={Apps} />
                <Router.Route path='/store' component={Store} />
                <Router.Route path='/vpn' component={Vpn} />
                <Router.Route path='/vpn/list_logins/:username' component={VpnLogins} />
                <Router.Route path='/triggers' component={Triggers} />
                <Router.Route path='/ts_status' component={Ts_status} />
                <Router.Route path='/panel/:id/:instance' component={Panel} />
                <Router.Route path='/subpanel/:id/:instance/:username' component={Subpanel} />
                <Router.Route path='/chart_panel/:instance/:host/:service' component={ChartPanel} />
            </Router.Route>
            <Router.Route path='/login' component={Login} />
        </Router.Router>
    );
  }
});

document.addEventListener('DOMContentLoaded', function() {
  var el = document.getElementById('body-wrapper');
  ReactDOM.render(<Provider store={store}>
        <App/>
      </Provider>, el);
});
