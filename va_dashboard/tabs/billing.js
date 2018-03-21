import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
import {connect} from 'react-redux';
var Network = require('../network');
import { PivotTable } from './shared_components';

class Billing extends Component{
    constructor (props) {
        super(props);
        this.state = {
            config: {}
        };
    }

    componentDidMount () {
        Network.get('/api/providers/billing', this.props.auth.token, {}).done(config => {
            this.setState({config});
        });
    }

    render() {
        let table = 'dataSource' in this.state.config ? <PivotTable {... this.state.config} /> : null;
        return (
            <div>
                <h4>Billing</h4>
                {table}
            </div>
        );
    }
}


module.exports = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Billing);
