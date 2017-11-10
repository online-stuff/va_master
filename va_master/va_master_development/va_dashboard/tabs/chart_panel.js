var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');
var widgets = require('./main_components');

var ChartPanel = React.createClass({
    getInitialState: function () {
        return {
            template: {
                "title": "",
                "help_url": "",
                "content": []
            },
            "host": "",
            "service": ""
        };
    },

    getPanel: function (instance, host, service) {
        var me = this, id = 'monitoring.chart';
        var data = {'panel': id, 'instance_name': instance, 'host': host, 'service': service};
        console.log(data);
        this.props.dispatch({type: 'CHANGE_PANEL', panel: id, instance: instance});
        Network.get('/api/panels/get_panel', this.props.auth.token, data).done(function (data) {
            me.setState({template: data, host: host, service: service});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },

    componentDidMount: function () {
        this.getPanel(this.props.params.instance, this.props.params.host, this.props.params.service);
    },

    componentWillReceiveProps: function (nextProps) {
        if (nextProps.params.instance !== this.props.params.instance || nextProps.params.host !== this.props.params.host || nextProps.params.service !== this.props.params.service) {
            this.getPanel(nextProps.params.instance, nextProps.params.host, nextProps.params.service);
        }
    },

    render: function () {
        var chartElem = null, content = this.state.template.content;
        if(content.length > 0){
            var element = content[0];
            element.key = element.name;
            element.host = this.state.host;
            element.service = this.state.service;
            var ChartRedux = connect(function(state){
                var newstate = {auth: state.auth};
                if(typeof element.reducers !== 'undefined'){
                    var r = element.reducers;
                    for (var i = 0; i < r.length; i++) {
                        newstate[r[i]] = state[r[i]];
                    }
                }
                return newstate;
            })(widgets[element.type]);
            chartElem = React.createElement(ChartRedux, element);
        }

        return (
            <div key={this.props.params.id}>
                <Bootstrap.PageHeader>{this.state.template.title} <small>{this.props.params.instance}</small></Bootstrap.PageHeader>
                {chartElem}
            </div>
        );
    }

});

ChartPanel = connect(function(state){
    return {auth: state.auth, panel: state.panel, alert: state.alert};
})(ChartPanel);

module.exports = ChartPanel;

