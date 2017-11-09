var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');
var Router = require('react-router');
var Reactable = require('reactable');

var VpnStatus = React.createClass({
    getInitialState: function () {
        return {
            status: [],
        };
    },

    getCurrentVpns: function () {
        var me = this;
        Network.get('/api/apps/vpn_users', this.props.auth.token).done(function (data) {
            me.setState({status: data.status});
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
                <Reactable.Tr key={vpn['Common Name']}>
                    <Reactable.Td column="Name">{vpn['Common Name']}</Reactable.Td>
                    <Reactable.Td column="Connected since">{vpn['Connected Since']}</Reactable.Td>
                    <Reactable.Td column="Virtual IP">{vpn['Real Address']}</Reactable.Td>
                    <Reactable.Td column="Bytes in">{vpn['Bytes Received']}</Reactable.Td>
                    <Reactable.Td column="Bytes out">{vpn['Bytes Sent']}</Reactable.Td>
                </Reactable.Tr>
            );
        });

        return (
            <div>
                <Bootstrap.PageHeader>VPN status</Bootstrap.PageHeader>
                <Reactable.Table className="table table-striped" columns={['Name', 'Connected since', 'Virtual IP', 'Bytes in', 'Bytes out']} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={['Name', 'Connected since', 'Virtual IP', 'Bytes in', 'Bytes out']}>
                    {status_rows}
                </Reactable.Table>
            </div>
        );
    }
});

VpnStatus = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(VpnStatus);

module.exports = VpnStatus;
