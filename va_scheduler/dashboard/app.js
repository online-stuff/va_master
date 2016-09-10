var React = require('react');
var ReactDOM = require('react-dom');
var Router = require('react-router');
var Redux = require('redux');
var ReactRedux = require('react-redux');

var connect = ReactRedux.connect;
var Provider = ReactRedux.Provider;

function auth(state, action){
    if(typeof state === 'undefined'){
        return {token: window.localStorage.getItem('token')};
    }

    var newState = Object.assign({}, state);
    if(action.type === 'LOGIN') {
        window.localStorage.setItem('token', action.token);
        newState.token = action.token;
        return newState;
    } else if(action.type === 'LOGOUT') {
        window.localStorage.removeItem('token');
        newState.token = null;
        return newState;
    } else {
        return state;
    }
};

var mainReducer = Redux.combineReducers({auth: auth});
var store = Redux.createStore(mainReducer);

var Home = require('./home').Home;
var Overview = require('./home').Overview;
var Hosts = require('./home').Hosts;
var Apps = require('./home').Apps;

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

document.addEventListener('DOMContentLoaded', () => {
  var el = document.getElementById('body-wrapper');
  ReactDOM.render(<Provider store={store}>
        <App/>
      </Provider>, el);
});
