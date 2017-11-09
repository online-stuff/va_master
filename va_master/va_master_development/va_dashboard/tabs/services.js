var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');
var Router = require('react-router');

var Billing = React.createClass({
    getInitialState: function () {
        return {
            logs: []
        }
    },

    render: function () {
        return ( <div> </div> );
    }
});


Billing = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Billing);

module.exports = Billing;
