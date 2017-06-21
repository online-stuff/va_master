var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');
var widgets = require('./main_components');

var Subpanel = React.createClass({
    getInitialState: function () {
        return {
            template: {
                "title": "",
                "help_url": "",
                "tbl_source": {},
                "content": []
            },
            username: ""
        };
    },

    getPanel: function (id, instance, username) {
        var me = this;
        var data = {'panel': id, 'instance_name': instance};
        console.log(data);
        this.props.dispatch({type: 'CHANGE_PANEL', panel: id, instance: instance, id: username});
        Network.get('/api/panels/get_panel', this.props.auth.token, data).done(function (data) {
            console.log(data.tbl_source);
            me.props.dispatch({type: 'ADD_DATA', tables: data.tbl_source});
            me.setState({template: data, username: username});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },

    componentDidMount: function () {
        this.getPanel(this.props.params.id, this.props.params.instance, this.props.params.username);
    },

    componentWillReceiveProps: function (nextProps) {
        if (nextProps.params.id !== this.props.params.id || nextProps.params.instance !== this.props.params.instance || nextProps.params.username !== this.props.params.username) {
            this.getPanel(nextProps.params.id, nextProps.params.instance, nextProps.params.username);
        }
    },

    componentWillUnmount: function () {
        this.props.dispatch({type: 'RESET_FILTER'});
    },

    render: function () {
        var redux = {};

        var elements = this.state.template.content.map(function(element) {
            element.key = element.name;
            if(Object.keys(redux).indexOf(element.type) < 0){
                var Component = widgets[element.type];
                redux[element.type] = connect(function(state){
                    var newstate = {auth: state.auth};
                    if(typeof element.reducers !== 'undefined'){
                        var r = element.reducers;
                        for (var i = 0; i < r.length; i++) {
                            newstate[r[i]] = state[r[i]];
                        }
                    }
                    return newstate;
                })(Component);
            }
            var Redux = redux[element.type];
            return React.createElement(Redux, element);
        });

        return (
            <div key={this.props.params.id}>
                <Bootstrap.PageHeader>{this.state.template.title + " for " + this.state.username} <small>{this.props.params.instance}</small></Bootstrap.PageHeader>
                {elements}
            </div>
        );
    }

});

Subpanel = connect(function(state){
    return {auth: state.auth, panel: state.panel, alert: state.alert, table: state.table};
})(Subpanel);

module.exports = Subpanel;
