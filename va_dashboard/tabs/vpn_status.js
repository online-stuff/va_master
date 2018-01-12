import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
import {connect} from 'react-redux';
var Network = require('../network');
import {Table, Tr, Td} from 'reactable';

var VpnStatus = React.createClass({
    getInitialState: function () {
        return {
            status: [],
            loading: true
        };
    },

    getCurrentVpns: function () {
        var me = this;
        Network.get('/api/apps/vpn_users', this.props.auth.token).done(function (data) {
            me.setState({status: data.status, loading: false});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },

    componentDidMount: function () {
        this.getCurrentVpns();
    },

    /*componentWillUnmount: function () {
        this.props.dispatch({type: 'RESET_TABS'});
    },*/

    render: function () {
        var status_rows = this.state.status.map(function(vpn) {
            return (
                <Tr key={vpn['Common Name']}>
                    <Td column="Name">{vpn['Common Name']}</Td>
                    <Td column="Connected since">{vpn['Connected Since']}</Td>
                    <Td column="Virtual IP">{vpn['Real Address']}</Td>
                    <Td column="Bytes in">{vpn['Bytes Received']}</Td>
                    <Td column="Bytes out">{vpn['Bytes Sent']}</Td>
                </Tr>
            );
        });
        var loading = this.state.loading;
        const spinnerStyle = {
            display: loading ? "block": "none",
        };
        const blockStyle = {
            visibility: loading ? "hidden": "visible",
        };

        return (
            <div className="app-containter">
                <span className="spinner" style={spinnerStyle} ><i className="fa fa-spinner fa-spin fa-3x" aria-hidden="true"></i></span>
                <div style={blockStyle} className="card">
                    <div className="card-body">
                        <Table className="table table-striped" columns={['Name', 'Connected since', 'Virtual IP', 'Bytes in', 'Bytes out']} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={['Name', 'Connected since', 'Virtual IP', 'Bytes in', 'Bytes out']} title="VPN status" filterClassName="form-control" filterPlaceholder="Filter">
                        {status_rows}
                        </Table>
                    </div>
                </div>
            </div>
        );
    }
});

VpnStatus = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(VpnStatus);

module.exports = VpnStatus;
