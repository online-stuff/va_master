import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
import {connect} from 'react-redux';
var Network = require('../network');
import {Table, Tr, Td} from 'reactable';
import { getSpinner } from './util';

class VpnStatus extends Component {
    constructor (props) {
        super(props);
        this.state = {
            status: [],
            loading: true
        };
        this.getCurrentVpns = this.getCurrentVpns.bind(this);
    }

    getCurrentVpns () {
        var me = this;
        Network.get('/api/apps/vpn_users', this.props.auth.token).done(function (data) {
            me.setState({status: data.status, loading: false});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }

    componentDidMount () {
        this.getCurrentVpns();
    }

    /*componentWillUnmount: function () {
        this.props.dispatch({type: 'RESET_TABS'});
    },*/

    render () {
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
        const blockStyle = {
            visibility: loading ? "hidden": "visible",
        };

        return (
            <div className="app-containter">
                {loading && getSpinner()}
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
}

VpnStatus = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(VpnStatus);

module.exports = VpnStatus;
