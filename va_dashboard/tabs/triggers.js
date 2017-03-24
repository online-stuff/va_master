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
    executeAction: function (rowNum, evtKey) {
        if(typeof evtKey !== 'undefined'){
            evtKey = 0;
        }
        var action = this.state.triggers[rowNum].actions[evtKey];
        var me = this;
        Network.post('/api/' + action.func, this.props.auth.token, action.kwargs).done(function(data) {
            console.log(data);
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },
    render: function () {
        var me = this;
        var trigger_rows = this.state.triggers.map(function(trigger, i) {
            var action;
            if(trigger.actions.length > 1){
                var actions = trigger.actions.map(function(a, j) {
                    return (
                        <Bootstrap.MenuItem key={j} eventKey={j}>{a.func}</Bootstrap.MenuItem>
                    );
                });
                action = (
                    <Bootstrap.DropdownButton bsStyle='primary' title="Choose" onSelect = {me.executeAction.bind(me, i)}>
                        {actions}
                    </Bootstrap.DropdownButton>
                );
            }else{
                action = (
                    <Bootstrap.Button type="button" bsStyle='primary' onClick={me.executeAction.bind(me, i)}>
                        {trigger.actions[0].func}
                    </Bootstrap.Button>
                );
            }
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
                        <div>{c.func + ": " + t + " " + me.state.operators[kwargs[t + "_operator"]] + " " + kwargs[t]}</div>
                    );
                });
                return c_divs;
            });
            return (
                <tr key={i}>
                    <td>{trigger.service}</td>
                    <td>{trigger.status}</td>
                    <td>{conditions}</td>
                    <td>{action}</td>
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

