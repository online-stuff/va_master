import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
import {connect} from 'react-redux';
var Network = require('../network');
import { PivotTable } from './shared_components';
import { getSpinner } from './util';

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
        let loaded = 'dataSource' in this.state.config;
        const spinnerStyle = {
            display: loaded ? "none" : "block"
        };
        return (
            <div>
                {getSpinner(spinnerStyle)}
                {loaded && <div className="card">
                    <div className="card-body">
                        <h4>Billing</h4>
                        <PivotTable {... this.state.config} />
                    </div>
                </div>}
            </div>
        );
    }
}


module.exports = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Billing);
