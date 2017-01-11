var React = require('react');
var ReactDOM = require('react-dom');
var Router = require('react-router');
var Redux = require('redux');
var ReactRedux = require('react-redux');

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
        return {isOpen: false};
    }

    var newState = Object.assign({}, state);
    if(action.type == 'OPEN_MODAL'){
        newState.isOpen = true;
    }
    if(action.type == 'CLOSE_MODAL'){
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

// function form(state, action){
//     if(typeof state === 'undefined'){
//         return {data: {}, url: ""};
//     }
//
//     var newState = Object.assign({}, state);
//     console.log("IN APP");
//     console.log(action.type);
//     console.log(newState);
//     if(action.type == 'UPDATE_FORM'){
//         newState.data = action.data;
//         console.log(action.data);
//     }
//     else if(action.type == 'SEND_FORM'){
//         newState.url = action.url;
//         console.log(action.url);
//     }
//     else if(action.type == 'RESET_FORM'){
//         newState.data = {};
//     }
//
//     return newState;
// };

var mainReducer = Redux.combineReducers({auth: auth, table: table, modal: modal, apps: apps});
var store = Redux.createStore(mainReducer);

var Home = require('./tabs/home');
var Overview = require('./tabs/overview');
var Hosts = require('./tabs/hosts');
var Apps = require('./tabs/apps');
var Store = require('./tabs/store');
var Panel = require('./tabs/panel');
var Vpn = require('./tabs/vpn');

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
                <Router.Route path='/panel/:id/:instance' component={Panel} />
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
