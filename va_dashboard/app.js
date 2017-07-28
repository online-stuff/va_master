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
        // newState.path = [];
    }
    if(action.type == 'CHANGE_DATA'){
        newState[action.name] = action.data;
        if("passVal" in action){
            newState["path"].push(action.passVal);
        }else if("initVal" in action){
            newState["path"] = action.initVal;
        }
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
        return {isOpen: false, template: { title: "", content: [], buttons: [], args: []}, args: {}, modalType: ""};
    }

    var newState = Object.assign({}, state);
    if(action.type == 'OPEN_MODAL'){
        if("template" in action)
            newState.template = action.template;
        if("args" in action){
            newState.args = action.args;
        }
        if("modalType" in action){
            newState.modalType = action.modalType;
        }
        newState.isOpen = true;
    }
    if(action.type == 'CLOSE_MODAL'){
        newState.template = { title: "", content: [], buttons: [], args: []};
        newState.args = {};
        newState.isOpen = false;
        newState.modalType = "";
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
        return {panel: '', instance: '', args: ''};
    }

    var newState = Object.assign({}, state);
    if(action.type == 'CHANGE_PANEL'){
        newState.panel = action.panel;
        newState.instance = action.instance;
        if('args' in action){
            newState.args = action.args;
        }else{
            newState.args = "";
        }
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
        return {readonly: {}, dropdowns: {}};
    }

    var newState = Object.assign({}, state);
    if(action.type == 'SET_READONLY'){
        newState.readonly = action.readonly;
    }
    if(action.type == 'RESET_FORM'){
        newState.readonly = {};
    }
    if(action.type == 'ADD_DROPDOWN'){
        newState.dropdowns = action.dropdowns;
    }
    if(action.type == 'SELECT'){
        newState.dropdowns[action.name].select = action.select;
    }
    if(action.type == 'RESET_SELECTION'){
        newState.dropdowns[action.name].select = "";
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
var Log = require('./tabs/log');
var Billing = require('./tabs/billing');

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
                <Router.Route path='/log' component={Log} />
                <Router.Route path='/billing' component={Billing} />
                <Router.Route path='/panel/:id/:instance(/:args)' component={Panel} />
                <Router.Route path='/subpanel/:id/:instance/:args' component={Subpanel} />
                <Router.Route path='/chart_panel/:instance/:host/:service' component={ChartPanel} />
            </Router.Route>
            <Router.Route path='/login' component={Login} />
        </Router.Router>
    );
  }
});

var activeCallback = $.Callbacks();

WebFontConfig = {
    custom: {
        families: ['Glyphicons Halflings', 'FontAwesome'],
        urls: ['static/css/bootstrap.min.css', 'static/css/font-awesome.min.css', 'static/css/style.css']
    },
    active: function () { activeCallback.fire(); },
    inactive: function () { console.log("inactive fonts"); }
};
(function() {
    var el = document.getElementById('body-wrapper');
    activeCallback.add(function (){
        ReactDOM.render(<Provider store={store}>
              <App/>
            </Provider>, el);
    });
    var wf = document.createElement('script');
    wf.src = ('https:' == document.location.protocol ? 'https' : 'http') +
      '://ajax.googleapis.com/ajax/libs/webfont/1.6.26/webfont.js';
    wf.type = 'text/javascript';
    wf.async = 'true';
    var s = document.getElementsByTagName('script')[0];
    s.parentNode.insertBefore(wf, s);
})();
