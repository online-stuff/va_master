var React = require('react');
var connect = require('react-redux').connect;
var Network = require('../network');

var Store = React.createClass({
    getInitialState: function () {
        return {states: []};
    },

    componentDidMount: function () {
        var me = this;
        Network.get('/api/states', this.props.auth.token).done(function (data) {
            console.log(data);
            me.setState({states: data});
        });
    },

    render: function () {
        var states_rows = this.state.states.map(function(state) {
            return (
                <div id = {state.name}>
                    State name: {state.name}
                    Description: {state.description}
                </div>
            )
        });

        return (
            <div>
                <h1>Manage states and minions</h1>
                {states_rows}
            </div>
        );
    }
});

Store = connect(function(state){
    return {auth: state.auth};
})(Store);

module.exports = Store;
