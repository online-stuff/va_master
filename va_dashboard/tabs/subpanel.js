import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
import {connect} from 'react-redux';
var Network = require('../network');
var widgets = require('./main_components');

class Subpanel extends Component {
    constructor (props) {
        super(props);
        this.state = {
            template: {
                "title": "",
                "help_url": "",
                "tbl_source": {},
                "content": []
            },
            args: ""
        };
        this.getPanel = this.getPanel.bind(this);
    }

    getPanel (id, server, args) {
        args = args.indexOf(',') > -1 ? args.split(",") : args;
        var data = {'panel': id, 'server_name': server, 'args': args};
        this.props.dispatch({type: 'CHANGE_PANEL', panel: id, server: server, args: args});
        Network.post('/api/panels/get_panel', this.props.auth.token, data).done(data => {
            this.props.dispatch({type: 'ADD_DATA', tables: data.tbl_source});
            if(typeof data.form_source !== 'undefined'){
                this.props.dispatch({type: 'ADD_DROPDOWN', dropdowns: data.form_source});
            }
            this.setState({template: data, args: args});
        }).fail(msg => {
            this.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }

    componentDidMount () {
        this.getPanel(this.props.params.id, this.props.params.server, this.props.params.args);
    }

    componentWillReceiveProps (nextProps) {
        if (nextProps.params.id !== this.props.params.id || nextProps.params.server !== this.props.params.server || nextProps.params.args !== this.props.params.args) {
            this.getPanel(nextProps.params.id, nextProps.params.server, nextProps.params.args);
        }
    }

    componentWillUnmount () {
        this.props.dispatch({type: 'RESET_FILTER'});
    }

    render () {
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

}

module.exports = connect(function(state){
    return {auth: state.auth, panel: state.panel, alert: state.alert, table: state.table};
})(Subpanel);

