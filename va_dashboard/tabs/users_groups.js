import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
import {connect} from 'react-redux';
var Network = require('../network');
var Groups = require('./users').Group;
import { getSpinner } from './util';

class GroupPanel extends Component {
    constructor (props) {
        super(props);
        this.state = {
            funcs: [],
            groups: [],
            group_opt: [],
            loading: true
        };
        this.getCurrentFuncs = this.getCurrentFuncs.bind(this);
    }

    getCurrentFuncs () {
        var me = this;
        var n1 = Network.get('/api/panels/get_all_functions', this.props.auth.token)
        .fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
        var n2 = Network.get('/api/panels/get_all_function_groups', this.props.auth.token)
        .fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
        $.when( n1, n2 ).done(function ( resp1, resp2 ) {
            var groups = resp2.map(function(group) {
                return {value: group.func_name, label: group.func_name};
            });
            me.setState({funcs: resp1, groups: resp2, group_opt: groups, loading: false});
        }); 
    }

    componentDidMount () {
        this.getCurrentFuncs();
    }

    render () {
        var GroupRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        })(Groups);

        var loading = this.state.loading;
        const blockStyle = {
            visibility: loading ? "hidden": "visible",
            position: 'relative'
        };

        return (
            <div className="app-containter">
                {loading && getSpinner()}
                <GroupRedux funcs = {this.state.funcs} groups = {this.state.groups} style={blockStyle} />
            </div>
        )
    }
}


module.exports = connect(state => {
    return {auth: state.auth, alert: state.alert};
})(GroupPanel);
