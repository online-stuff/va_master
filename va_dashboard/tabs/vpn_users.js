var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');
var Router = require('react-router');
var Reactable = require('reactable');

var VpnUsers = React.createClass({
    getInitialState: function () {
        return {
            active: [],
            revoked: [],
            loading: true,
        };
    },

    getCurrentVpns: function () {
        var me = this;
        Network.get('/api/apps/vpn_users', this.props.auth.token).done(function (data) {
            me.setState({active: data.active, revoked: data.revoked, loading: false});
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

    /*componentWillUnmount: function () {
        this.props.dispatch({type: 'RESET_TABS'});
    },*/

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
        var a_len = active_rows.length, r_len = revoked_rows.length;
        var rowNum = a_len > r_len ? r_len : a_len;
        rowNum = rowNum > 10 ? 10 : rowNum;

        var ModalRedux = connect(function(state){
            return {auth: state.auth, modal: state.modal, alert: state.alert};
        })(Modal);
        var sf_cols = ['Name', 'Connected'];

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
                <ModalRedux addVpn = {this.addVpn} />
                <div style={blockStyle} className="container-block">
                    <div className="block card">
                        <div className="card-body">
                            <Reactable.Table className="table table-striped" columns={['Name', 'Connected', 'Actions']} itemsPerPage={rowNum} pageButtonLimit={10} noDataText="No matching records found." sortable={sf_cols} filterable={sf_cols} btnName="Add user" btnClick={this.openModal} title="Active users" filterClassName="form-control custpm-filter-input" filterPlaceholder="Filter">
                                {active_rows}
                            </Reactable.Table>
                        </div>
                    </div>
                    <div className="block card">
                        <div className="card-body">
                            <Reactable.Table id="revoked-tbl" className="table table-striped" columns={['Name', 'Connected']} itemsPerPage={rowNum} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={['Name', 'Connected']} title="Revoked users" filterClassName="form-control custpm-filter-input" filterPlaceholder="Filter">
                                {revoked_rows}
                            </Reactable.Table>
                        </div>
                    </div>
                </div>
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

VpnUsers = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(VpnUsers);

module.exports = VpnUsers;
