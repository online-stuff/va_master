var React = require('react');
var Network = require('../network');
var connect = require('react-redux').connect;

var Hosts = React.createClass({
    getInitialState: function () {
        return {hosts: []};
    },
    componentDidMount: function () {
        var me = this;
        Network.get('/api/hosts', this.props.auth.token).done(function (data) {
            me.setState({hosts: data.hosts});
        });
    },
    render: function() {
        var host_rows = this.state.hosts.map(function(host) {
            return <tr key={host.name}>
                <td>{host.name}</td>
                <td>{host.driver}</td>
                <td>{host.is_deletable ? 'Delete' : '(this host)'}</td>
            </tr>
        });
        var NewHostFormRedux = connect(function(state){
            return {auth: state.auth};
        })(NewHostForm);

        return (<div>
            <h1>Add new host</h1>
            <NewHostFormRedux />
            <h1>Current hosts</h1>
            <table className='table table-striped' style={{width: '100%'}}>
            <thead>
                <tr>
                    <td>Host name</td>
                    <td>Driver</td>
                    <td>Actions</td>
                </tr>
            </thead>
            <tbody>
            {host_rows}
            </tbody>
            </table>
        </div>);
    }
});


var NewHostForm = React.createClass({
    getInitialState: function () {
        return {currentDriver: 'Openstack'};
    },
    render: function () {
        var drivers = ['Openstack', 'AWS', 'LibVirt'].map(function(driver) {
            return <option key={driver} value={driver}>{driver}</option>;
        });
        var inputs = null;
        if(this.state.currentDriver == 'Openstack') {
            inputs = ['Openstack host url', 'User', 'Password', 'Tenant'];
        }else if(this.state.currentDriver == 'AWS'){
            inputs = ['AWS token', 'AWS secret'];
        }else{
            inputs = ['Libvirt username', 'Libvirt password', 'Libvirt port'];
        }
        inputs = inputs.map(function(n){
            return <div key={n}><input placeholder={n} /><br/></div>
        });

        return (
        <form onSubmit={this.onSubmit}>
            <select onChange={this.onChange}>
                {drivers}
            </select>
            <div><input ref='hostname' placeholder='Host Name' /> <br/></div>
            {inputs}
            <button>Add</button>
        </form>);
    },
    onChange: function (event) {
        this.setState({currentDriver: event.target.value})
    },
    onSubmit: function(e) {
        e.preventDefault();
        var data = {name: this.refs.hostname.value, driver: this.state.currentDriver};
        Network.post('/api/hosts', this.props.auth.token, data);
    }
});

Hosts = connect(function(state){
    return {auth: state.auth};
})(Hosts);

module.exports = Hosts;
