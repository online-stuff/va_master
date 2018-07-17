import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
import {connect} from 'react-redux';
var Network = require('../network');
import {findDOMNode} from 'react-dom';
import {hashHistory} from 'react-router';
import {Table, Tr, Td} from 'reactable';
import { getSpinner } from './util';

class VpnUsers extends Component {
    constructor (props) {
        super(props);
        this.state = {
            active: [],
            revoked: [],
            loading: true,
        };
        this.getCurrentVpns = this.getCurrentVpns.bind(this);
        this.addVpn = this.addVpn.bind(this);
        this.btn_clicked = this.btn_clicked.bind(this);
        this.openModal = this.openModal.bind(this);
    }

    getCurrentVpns () {
        var me = this;
        Network.get('/api/apps/vpn_users', this.props.auth.token).done(function (data) {
            me.setState({active: data.active, revoked: data.revoked, loading: false});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }

    addVpn (username) {
        this.setState({active: this.state.active.concat([{"connected": false, "name": username}])});
    }

    componentDidMount () {
        this.getCurrentVpns();
    }

    /*componentWillUnmount: function () {
        this.props.dispatch({type: 'RESET_TABS'});
    },*/

    btn_clicked (username, evtKey) {
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
                hashHistory.push('/vpn/list_logins/' + username);
                break;
            default:
                break;
        }
    }

    openModal() {
        this.props.dispatch({type: 'OPEN_MODAL'});
    }

    render () {
        var active_rows = this.state.active.filter(function(vpn) {
            if(this.state.revoked.indexOf(vpn.name) > -1){
                return false;
            }
            return true;
        }.bind(this)).map(function(vpn, i) {
            return (
                <Tr key={vpn.name}>
                    <Td column="Name">{vpn.name}</Td>
                    <Td column="Connected">{vpn.connected?"True":"False"}</Td>
                    <Td column="Actions">
                        <Bootstrap.DropdownButton id={"dropdown-" + vpn.name} bsStyle='default' title="Choose" onSelect = {this.btn_clicked.bind(this, vpn.name)}>
                            <Bootstrap.MenuItem eventKey="download">Download certificate</Bootstrap.MenuItem>
                            <Bootstrap.MenuItem eventKey="revoke">Revoke user</Bootstrap.MenuItem>
                            <Bootstrap.MenuItem eventKey="list">List logins</Bootstrap.MenuItem>
                        </Bootstrap.DropdownButton>
                    </Td>
                </Tr>
            );
        }.bind(this));

        var revoked_rows = this.state.revoked.map(function(vpn) {
            return (
                <Tr key={vpn}>
                    <Td column="Name">{vpn}</Td>
                    <Td column="Connected">False</Td>
                </Tr>
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
        const blockStyle = {
            visibility: loading ? "hidden": "visible",
        };

        return (
            <div className="app-containter">
                {loading && getSpinner()}
                <ModalRedux addVpn = {this.addVpn} />
                <div style={blockStyle} className="container-block">
                    <div className="block card">
                        <div className="card-body">
                            <Table className="table table-striped" columns={['Name', 'Connected', 'Actions']} itemsPerPage={rowNum} pageButtonLimit={10} noDataText="No matching records found." sortable={sf_cols} filterable={sf_cols} buttons={[{name: "Add user", onClick: this.openModal, icon: 'glyphicon glyphicon-plus'}]} title="Active users" filterClassName="form-control custpm-filter-input" filterPlaceholder="Filter">
                                {active_rows}
                            </Table>
                        </div>
                    </div>
                    <div className="block card">
                        <div className="card-body">
                            <Table id="revoked-tbl" className="table table-striped" columns={['Name', 'Connected']} itemsPerPage={rowNum} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={['Name', 'Connected']} title="Revoked users" filterClassName="form-control custpm-filter-input" filterPlaceholder="Filter">
                                {revoked_rows}
                            </Table>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

class Modal extends Component {

    open() {
        this.props.dispatch({type: 'OPEN_MODAL'});
    }

    close() {
        this.props.dispatch({type: 'CLOSE_MODAL'});
    }

    action(e) {
        console.log(e.target);
        console.log(this.refs.forma);
        console.log(findDOMNode(this.refs.forma).elements);
        var elements = findDOMNode(this.refs.forma).elements;
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
    }

    render () {
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
}

VpnUsers = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(VpnUsers);

module.exports = VpnUsers;
