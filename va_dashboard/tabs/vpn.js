var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');
var Router = require('react-router');
var Reactable = require('reactable');

var Vpn = React.createClass({
    getInitialState: function () {
        return {
            active: [],
            revoked: [],
            status: [],
        };
    },

    getCurrentVpns: function () {
        var me = this;
        Network.get('/api/apps/vpn_users', this.props.auth.token).done(function (data) {
            me.setState({active: data.active, revoked: data.revoked, status: data.status});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },

    addVpn: function (username) {
        this.setState({active: this.state.active.concat([{"connected": false, "name": username}])});
    },

    componentDidMount: function () {
        this.getCurrentVpns();
    },

    btn_clicked: function(username, evtKey){
        var data = {username: username};
        var me = this;
        switch (evtKey) {
            case "download":
                Network.download_file("/api/apps/download_vpn_cert", this.props.auth.token, data).done(function(d) {
                    var data = new Blob([d], {type: 'octet/stream'});
                    var url = window.URL.createObjectURL(data);
                    tempLink = document.createElement('a');
                    tempLink.style = "display: none";
                    tempLink.href = url;
                    tempLink.setAttribute('download', 'certificate.txt');
                    document.body.appendChild(tempLink);
                    tempLink.click();
                    setTimeout(function(){
                        document.body.removeChild(tempLink);
                        window.URL.revokeObjectURL(url);
                    }, 100);
                }).fail(function (msg) {
                    me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
                });
                break;
            case "revoke":
                Network.post("/api/apps/revoke_vpn_user", this.props.auth.token, data).done(function(d) {
                    if(d === true){
                        me.setState({revoked: me.state.revoked.concat([username])});
                    }
                }).fail(function (msg) {
                    me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
                });
                break;
            case "list":
                Router.hashHistory.push('/vpn/list_logins/' + username);
                break;
            default:
                break;
        }
    },

    openModal: function() {
        this.props.dispatch({type: 'OPEN_MODAL'});
    },

    render: function () {
        var active_rows = this.state.active.filter(function(vpn) {
            if(this.state.revoked.indexOf(vpn.name) > -1){
                return false;
            }
            return true;
        }.bind(this)).map(function(vpn, i) {
            return (
                <Reactable.Tr key={vpn.name}>
                    <Reactable.Td column="Name">{vpn.name}</Reactable.Td>
                    <Reactable.Td column="Connected">{vpn.connected?"True":"False"}</Reactable.Td>
                    <Reactable.Td column="Actions">
                        <Bootstrap.DropdownButton id={"dropdown-" + vpn.name} bsStyle='default' title="Choose" onSelect = {this.btn_clicked.bind(this, vpn.name)}>
                            <Bootstrap.MenuItem eventKey="download">Download certificate</Bootstrap.MenuItem>
                            <Bootstrap.MenuItem eventKey="revoke">Revoke user</Bootstrap.MenuItem>
                            <Bootstrap.MenuItem eventKey="list">List logins</Bootstrap.MenuItem>
                        </Bootstrap.DropdownButton>
                    </Reactable.Td>
                </Reactable.Tr>
            );
        }.bind(this));

        var revoked_rows = this.state.revoked.map(function(vpn) {
            return (
                <Reactable.Tr key={vpn}>
                    <Reactable.Td column="Name">{vpn}</Reactable.Td>
                    <Reactable.Td column="Connected">False</Reactable.Td>
                </Reactable.Tr>
            );
        });

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

        var ModalRedux = connect(function(state){
            return {auth: state.auth, modal: state.modal, alert: state.alert};
        })(Modal);

        return (
            <div>
                <Bootstrap.PageHeader>VPN status</Bootstrap.PageHeader>
                <Reactable.Table className="table striped" columns={['Name', 'Connected since', 'Virtual IP', 'Bytes in', 'Bytes out']} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={['Name', 'Connected since', 'Virtual IP', 'Bytes in', 'Bytes out']}>
                    {status_rows}
                </Reactable.Table>
                <Bootstrap.PageHeader>VPN Users</Bootstrap.PageHeader>
                <h4>Active users</h4>
                <Bootstrap.Button type="button" bsStyle='default' className="pull-right margina" onClick={this.openModal}>
                    <Bootstrap.Glyphicon glyph='plus' />
                    Add user
                </Bootstrap.Button>
                <ModalRedux addVpn = {this.addVpn} />
                <Reactable.Table className="table striped" columns={['Name', 'Connected', 'Actions']} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={['Name', 'Connected']} >
                    {active_rows}
                </Reactable.Table>
                <h4>Revoked users</h4>
                <Reactable.Table className="table striped" columns={['Name', 'Connected']} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={['Name', 'Connected']}>
                    {revoked_rows}
                </Reactable.Table>
            </div>
        );
    }
});

var Modal = React.createClass({

    open: function() {
        this.props.dispatch({type: 'OPEN_MODAL'});
    },

    close: function() {
        this.props.dispatch({type: 'CLOSE_MODAL'});
    },

    action: function(e) {
        console.log(e.target);
        console.log(this.refs.forma);
        console.log(ReactDOM.findDOMNode(this.refs.forma).elements);
        var elements = ReactDOM.findDOMNode(this.refs.forma).elements;
        var data = {};
        for(i=0; i<elements.length; i++){
            data[elements[i].name] = elements[i].value;
        }
        console.log(data);
        var me = this;
        Network.post("/api/apps/add_vpn_user", this.props.auth.token, data).done(function(d) {
            if(d === true){
                me.props.addVpn(data['username']);
            }
            me.props.dispatch({type: 'CLOSE_MODAL'});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },

    render: function () {
        return (
            <Bootstrap.Modal show={this.props.modal.isOpen} onHide={this.close}>
            <Bootstrap.Modal.Header closeButton>
              <Bootstrap.Modal.Title>Create VPN</Bootstrap.Modal.Title>
            </Bootstrap.Modal.Header>

            <Bootstrap.Modal.Body>
                <div className="left">
                    <Bootstrap.Form ref="forma">
                        <Bootstrap.FormControl type='text' name="username" placeholder="Name" />
                        {/* <Bootstrap.FormControl type='text' name="Description" placeholder="Description" /> */}
                    </Bootstrap.Form>
                </div>
                <div className="right">
                    <h3>Fill the form to add new vpn</h3>
                    <div></div>
                </div>
            </Bootstrap.Modal.Body>

            <Bootstrap.Modal.Footer>
              <Bootstrap.Button onClick={this.close}>Cancel</Bootstrap.Button>
              <Bootstrap.Button onClick={this.action} bsStyle = "primary">Add user</Bootstrap.Button>
            </Bootstrap.Modal.Footer>

        </Bootstrap.Modal>
        );
    }
});

Vpn = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Vpn);

module.exports = Vpn;
