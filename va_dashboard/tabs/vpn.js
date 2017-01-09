var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');
var Router = require('react-router');

var Vpn = React.createClass({
    getInitialState: function () {
        return {
            active: [],
            revoked: [],
            status: [],
            checkall: false
        };
    },

    checkAll: function () {
        var check = !this.state.checkall;
        this.setState({checkall: check});
        var active = this.state.active.map(function(vpn) {
            vpn.check = check;
            return vpn;
        });
        this.setState({active: active});
    },

    changeCheck: function (i, evt) {
        var active = this.state.active;
        active[i].check = evt.target.checked;
        this.setState({checkall: false});
        this.setState({active: active});
    },

    getCurrentVpns: function () {
        var me = this;
        Network.get('/api/apps/vpn_users', this.props.auth.token).done(function (data) {
            me.setState({active: data.active});
            me.setState({revoked: data.revoked});
        });
    },

    componentDidMount: function () {
        this.getCurrentVpns();
    },

    btn_clicked: function(id, evtKey){
        console.log(id);
        console.log(evtKey);
        // var data = {id: id, action: evtKey};
        // Network.post('/api/vpn', this.props.auth.token, data).done(function(d) {
        //     console.log(d);
        // });
    },

    openModal: function() {
        this.props.dispatch({type: 'OPEN_MODAL'});
    },

    render: function () {
        var active_rows = this.state.active.map(function(vpn, i) {
            return (
                <tr key={vpn.name}>
                    <td><input type="checkbox" checked={this.state.checkall || this.state.active[i].check} onChange = {this.changeCheck.bind(this, i)} /></td>
                    <td>{vpn.name}</td>
                    <td>{vpn.connected}</td>
                    <td>
                        <Bootstrap.DropdownButton bsStyle='default' title="Choose" onSelect = {this.btn_clicked.bind(this, vpn.name)}>
                            <Bootstrap.MenuItem eventKey="download">Download certificate</Bootstrap.MenuItem>
                            <Bootstrap.MenuItem eventKey="revoke">Revoke user</Bootstrap.MenuItem>
                            <Bootstrap.MenuItem eventKey="list">List logins</Bootstrap.MenuItem>
                        </Bootstrap.DropdownButton>
                    </td>
                </tr>
            );
        }.bind(this));

        var revoked_rows = this.state.revoked.map(function(vpn) {
            return (
                <tr key={vpn.name}>
                    <td>{vpn.name}</td>
                    <td>{vpn.connected}</td>
                </tr>
            );
        });

        var status_rows = this.state.status.map(function(vpn) {
            return (
                <tr key={vpn.name}>
                    <td>{vpn.name}</td>
                    <td>{vpn.connected}</td>
                    <td>{vpn.ip}</td>
                    <td>{vpn.bytes_in}</td>
                    <td>{vpn.bytes_out}</td>
                </tr>
            );
        });

        var ModalRedux = connect(function(state){
            return {auth: state.auth, modal: state.modal};
        })(Modal);

        return (
            <div>
                <Bootstrap.PageHeader>VPN Users</Bootstrap.PageHeader>
                <h4>Active users</h4>
                <Bootstrap.Button type="button" bsStyle='default' className="pull-right margina" onClick={this.openModal}>
                    <Bootstrap.Glyphicon glyph='plus' />
                    Add user
                </Bootstrap.Button>
                <ModalRedux />
                <Bootstrap.Table striped bordered hover>
                    <thead>
                        <tr>
                            <td><input type="checkbox" checked={this.state.checkall} onChange={this.checkAll} /></td>
                            <td>Name</td>
                            <td>Connected</td>
                            <td>Actions</td>
                        </tr>
                    </thead>
                    <tbody>
                        {active_rows}
                    </tbody>
                </Bootstrap.Table>
                <h4>Revoked users</h4>
                <Bootstrap.Table striped bordered hover>
                    <thead>
                        <tr>
                        <td>Name</td>
                        <td>Connected</td>
                        </tr>
                    </thead>
                    <tbody>
                        {revoked_rows}
                    </tbody>
                </Bootstrap.Table>
                <Bootstrap.PageHeader>VPN status</Bootstrap.PageHeader>
                <Bootstrap.Table striped bordered hover>
                    <thead>
                        <tr>
                        <td>Name</td>
                        <td>Connected since</td>
                        <td>IP address</td>
                        <td>Bytes in</td>
                        <td>Bytes out</td>
                        </tr>
                    </thead>
                    <tbody>
                        {status_rows}
                    </tbody>
                </Bootstrap.Table>
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
        //Network.post();
    },

    render: function () {
        var redux = {};
        return (
            <Bootstrap.Modal show={this.props.modal.isOpen} onHide={this.close}>
            <Bootstrap.Modal.Header closeButton>
              <Bootstrap.Modal.Title>Create VPN</Bootstrap.Modal.Title>
            </Bootstrap.Modal.Header>

            <Bootstrap.Modal.Body>
                <div className="left">
                    <Bootstrap.Form ref="forma">
                        <Bootstrap.FormControl type='text' name="Name" placeholder="Name" />
                        <Bootstrap.FormControl type='text' name="Description" placeholder="Description" />
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
    return {auth: state.auth};
})(Vpn);

module.exports = Vpn;
