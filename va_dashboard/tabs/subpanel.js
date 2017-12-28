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
            args: ""
        };
    },

    getPanel: function (id, server, args) {
        var me = this, args = args.indexOf(',') > -1 ? args.split(",") : args;
        var data = {'panel': id, 'server_name': server, 'args': args};
        console.log(data);
        this.props.dispatch({type: 'CHANGE_PANEL', panel: id, server: server, args: args});
        Network.post('/api/panels/get_panel', this.props.auth.token, data).done(function (data) {
            console.log(data.tbl_source);
            me.props.dispatch({type: 'ADD_DATA', tables: data.tbl_source});
            if(typeof data.form_source !== 'undefined'){
                me.props.dispatch({type: 'ADD_DROPDOWN', dropdowns: data.form_source});
            }
            me.setState({template: data, args: args});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },

    componentDidMount: function () {
        this.getPanel(this.props.params.id, this.props.params.server, this.props.params.args);
    },

    componentWillReceiveProps: function (nextProps) {
        if (nextProps.params.id !== this.props.params.id || nextProps.params.server !== this.props.params.server || nextProps.params.args !== this.props.params.args) {
            this.getPanel(nextProps.params.id, nextProps.params.server, nextProps.params.args);
        }
    },

    componentWillUnmount: function () {
        this.props.dispatch({type: 'RESET_FILTER'});
    },

    render: function () {
        var redux = {};
        var ModalRedux = connect(function(state){
            return {auth: state.auth, modal: state.modal, panel: state.panel, alert: state.alert};
        })(widgets.Modal);

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
                <Bootstrap.PageHeader>{this.state.template.title + " for " + this.state.args} <small>{this.props.params.server}</small></Bootstrap.PageHeader>
                {elements}
                <ModalRedux />
            </div>
        );
    }

});

Subpanel = connect(function(state){
    return {auth: state.auth, panel: state.panel, alert: state.alert, table: state.table};
})(Subpanel);

module.exports = Subpanel;
