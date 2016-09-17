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
            return {token: null, username: null};
        }
    }

    var newState = Object.assign({}, state);
    if(action.type === 'LOGIN') {
        newState.username = action.username;
        newState.token = action.token;
    } else if(action.type === 'LOGOUT') {
        newState.username = null;
        newState.token = null;
    }
    // Add into session
    window.localStorage.setItem('auth', JSON.stringify(newState));
    return newState;
};

var mainReducer = Redux.combineReducers({auth: auth});
var store = Redux.createStore(mainReducer);

var Home = require('./tabs/home');
var Overview = require('./tabs/overview');
var Hosts = require('./tabs/hosts');
var Apps = require('./tabs/apps');

var Login = require('./login');
var App = React.createClass({
  render: function() {
    return (
        <Router.Router history={Router.hashHistory}>
            <Router.Route path='/' component={Home}>
                <Router.IndexRoute component={Overview} />
                <Router.Route path='/hosts' component={Hosts} />
                <Router.Route path='/apps' component={Apps} />
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
