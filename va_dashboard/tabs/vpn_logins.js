var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');


var VpnLogins = React.createClass({
    getInitialState: function () {
        return {
            logins: []
        };
    },

    componentDidMount: function () {
        this.get_logins();
    },

    get_logins: function() {
        var data = {username: this.props.params.username};
        Network.post("/api/apps/list_user_logins", this.props.auth.token, data).done(function(d) {
            console.log(d);
            if(Array.isArray(d) && d.length > 0){
                this.setState({logins: d});
            }else{
                this.setState({logins: [{date: '10.01.2017', ip: '192.168.80.60'}, {date: '11.01.2017', ip: '192.168.80.70'}]});
            }
        }.bind(this));
    },

    render: function () {
        var rows = this.state.logins.map(function(login) {
            return (
                <tr key={login.ip}>
                    <td>{login.date}</td>
                    <td>{login.ip}</td>
                </tr>
            );
        });
        return (
            <div>
            <Bootstrap.PageHeader>List of logins</Bootstrap.PageHeader>
            <Bootstrap.Table striped bordered hover>
                <thead>
                    <tr>
                    <td>Login date</td>
                    <td>Ip address</td>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </Bootstrap.Table>
        </div>
        );
    }
});

VpnLogins = connect(function(state){
    return {auth: state.auth};
})(VpnLogins);

module.exports = VpnLogins;
