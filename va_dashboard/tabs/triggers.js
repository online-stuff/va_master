var React = require('react');
var Bootstrap = require('react-bootstrap');
var Network = require('../network');
var connect = require('react-redux').connect;

var Triggers = React.createClass({
    getInitialState: function () {
        return {triggers: [], operators: {'lt': '<', 'gt': '>', 'ge': '>=', 'le': '<='}};
    },
    getCurrentTriggers: function () {
        var me = this;
        Network.get('/api/triggers', this.props.auth.token).done(function (data) {
            me.setState({triggers: data["va-clc"]});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },
    componentDidMount: function () {
        this.getCurrentTriggers();
    },
    render: function () {
        var me = this;
        var trigger_rows = this.state.triggers.map(function(trigger, i) {
            var conditions = trigger.conditions.map(function(c, j) {
                var kwargs = c.kwargs;
                var all_keys = Object.keys(kwargs);
                var main_keys = all_keys.filter(function(key) {
                    if(key.indexOf('operator') > -1){
                        return false;
                    }
                    return true;
                });
                var c_divs = main_keys.map(function(t){
                    return (
                        <div key={j}>{c.func + ": " + t + " " + me.state.operators[kwargs[t + "_operator"]] + " " + kwargs[t]}</div>
                    );
                });
                return c_divs;
            });
            var actions = trigger.actions.map(function(a, j) {
                return (
                    <div key={j}>{a.func}</div>
                );
            });
            return (
                <tr key={i}>
                    <td>{trigger.service}</td>
                    <td>{trigger.status}</td>
                    <td>{conditions}</td>
                    <td>Terminal</td>
                    <td>{actions}</td>
                </tr>
            );
        });

        return (
            <div>
                <Bootstrap.PageHeader>List triggers</Bootstrap.PageHeader>
                <Bootstrap.Table striped bordered hover>
                    <thead>
                        <tr>
                        <td>Service</td>
                        <td>Status</td>
                        <td>Conditions</td>
                        <td>Target</td>
                        <td>Actions</td>
                        </tr>
                    </thead>
                    <tbody>
                        {trigger_rows}
                    </tbody>
                </Bootstrap.Table>
            </div>
        );
    }
});

Triggers = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Triggers);

module.exports = Triggers;

