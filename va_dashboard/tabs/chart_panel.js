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
            "provider": "",
            "service": ""
        };
    },

    getPanel: function (server, provider, service) {
        var me = this, id = 'monitoring.chart';
        var data = {'panel': id, 'server_name': server, 'provider': provider, 'service': service};
        console.log(data);
        this.props.dispatch({type: 'CHANGE_PANEL', panel: id, server: server});
        Network.get('/api/panels/get_panel', this.props.auth.token, data).done(function (data) {
            me.setState({template: data, provider: provider, service: service});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },

    componentDidMount: function () {
        this.getPanel(this.props.params.server, this.props.params.provider, this.props.params.service);
    },

    componentWillReceiveProps: function (nextProps) {
        if (nextProps.params.server !== this.props.params.server || nextProps.params.provider !== this.props.params.provider || nextProps.params.service !== this.props.params.service) {
            this.getPanel(nextProps.params.server, nextProps.params.provider, nextProps.params.service);
        }
    },

    render: function () {
        var chartElem = null, content = this.state.template.content;
        if(content.length > 0){
            var element = content[0];
            element.key = element.name;
            element.provider = this.state.provider;
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
                <Bootstrap.PageHeader>{this.state.template.title} <small>{this.props.params.server}</small></Bootstrap.PageHeader>
                {chartElem}
            </div>
        );
    }

});

ChartPanel = connect(function(state){
    return {auth: state.auth, panel: state.panel, alert: state.alert};
})(ChartPanel);

module.exports = ChartPanel;

