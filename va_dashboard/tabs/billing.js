import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
import {connect} from 'react-redux';
var Network = require('../network');
import { PivotTable } from './shared_components';

class Billing extends Component{
    constructor (props) {
        super(props);
        this.state = {
            config: {
				dataSource: [
                    {provider: 'provider', cpu: 4, memory: 8, hdd: 1000, cost: 10000, e_cost: 20000, subRows: [{server: 'server', cpu: 4, memory: 8, hdd: 1000, cost: 10000, e_cost: 20000}, {server: 'server2', cpu: 4, memory: 8, hdd: 1000, cost: 10000, e_cost: 20000}]},{provider: 'provider2', cpu: 4, memory: 8, hdd: 1000, cost: 10000, e_cost: 20000, subRows: [{server: 'server', cpu: 4, memory: 8, hdd: 1000, cost: 10000, e_cost: 20000}, {server: 'server3', cpu: 4, memory: 8, hdd: 1000, cost: 10000, e_cost: 20000}]}
				],
				rows    : [ {key: 'provider', label: 'Provider'}, {key: 'server', label: 'Server'} ],
				data    : [ {key: 'cpu', label: 'CPU', type: 'number'}, {key: 'memory', label: 'Memory', type: 'number'}, {key: 'hdd', label: 'HDD', type: 'number'}, {key: 'cost', label: 'Cost', type: 'number'}, {key: 'e_cost', label: 'Estimated cost', type: 'number'} ]
            }
        }
    }

    componentDidMount () {
    }

    render() {
        return ( <PivotTable {... this.state.config} /> );
    }
}


module.exports = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Billing);
