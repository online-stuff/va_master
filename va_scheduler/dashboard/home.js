var React = require('react');
var Router = require('react-router');
var connect = require('react-redux').connect;

var Home = React.createClass({
    componentDidMount: function() {
        if(!this.props.auth.token){
            Router.hashHistory.push('/login');
        }
    },
    componentWillReceiveProps: function(props) {
        if(!props.auth.token) {
            Router.hashHistory.push('/login');
        }
    },
    logOut: function () {
        this.props.dispatch({type: 'LOGOUT'});
    },
    render: function () {
        return (
        <div>
            <div className='top-header'>
                <img src='/static/logo.png' className='logo' style={{float: 'left'}}/>
                <button className='btn btn-default logout' onClick={this.logOut}>Logout</button>
                <div className='clearfix' />
            </div>
            <div className='sidebar'>
                <ul className='left-menu'>
                    <li><Router.IndexLink to='' activeClassName='active'>Overview</Router.IndexLink></li>
                    <li><Router.Link to='hosts' activeClassName='active'>Hosts</Router.Link></li>
                    <li><Router.Link to='apps' activeClassName='active'>Apps</Router.Link></li>
                </ul>
            </div>
            <div className='main-content'>
                {this.props.children}
            </div>
        </div>
        );
    }
});

var Overview = function (props) {
    var appblocks = [['Directory', 'fa-group'], ['Monitoring', 'fa-heartbeat'],
        ['Backup', 'fa-database'], ['OwnCloud', 'fa-cloud'], ['Fileshare', 'fa-folder-open'],
        ['Email', 'fa-envelope']];
    appblocks = appblocks.map(function(d){
        return (
            <div key={d[0]} className='app-block'>
                <div className='icon-wrapper'>
                    <i className={'fa ' + d[1]} />
                </div>
                <div className='name-wrapper'>
                    <h1>{d[0]}</h1>
                </div>
                <div className='clearfix' />
            </div>
        );
    });
    return <div>
        {appblocks}
        <div style={{clear: 'both'}} />
    </div>
};

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
        var data = JSON.stringify({name: this.refs.hostname.value, driver: this.state.currentDriver});
        $.ajax({
            type: 'POST',
            url: '/api/hosts',
            contentType: 'application/json',
            data: data
        });
    }
});

var Hosts = React.createClass({
    getInitialState: function () {
        return {hosts: []};
    },
    componentDidMount: function () {
        var me = this;
        $.ajax({
            type: 'GET',
            url: '/api/hosts'
        }).done(function (data) {
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
        return (<div>
            <h1>Add new host</h1>
            <NewHostForm />
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
})
var Apps = React.createClass({
    getInitialState: function () {
        return {status: 'none', progress: 0};
    },
    render: function () {
        var statusColor, statusDisplay, statusMessage;

        if(this.state.status == 'launching'){
            statusColor = 'yellow';
            statusDisplay = 'block';
            statusMessage = 'Launching... ' + this.state.progress + '%';
        }else if(this.state.status == 'launched'){
            statusColor = 'green';
            statusDisplay = 'block';
            statusMessage = 'Launched successfully!';
        }else {
            statusDisplay = 'none';
        }
        return (
            <div>
                <h1>Launch new app</h1>
                <form onSubmit={this.onSubmit} className='form-horizontal'>
                    <div className='form-group'>
                    <select>
                    </select> <br/>
                    <select>
                        <option>samba.sls</option>
                    </select>
                    <input placeholder='Instance name' ref='name'/> <br/>
                    <button>Launch</button>
                    <div style={{width: '100%', padding: 10, borderRadius: 5, background: statusColor, display: statusDisplay}}>
                        {statusMessage}
                    </div>
                    </div>
                </form>
            </div>
        );
    },
    onSubmit: function(e) {
        e.preventDefault();
        var me = this;
        this.setState({status: 'launching', progress: 0});
        interval = setInterval(function(){
            if(me.state.status == 'launching' && me.state.progress <= 80){
                var newProgress = me.state.progress + 10;
                me.setState({progress: newProgress})
            }else{
                clearInterval(interval);
            }
        }, 10000);
        var data = JSON.stringify({name: this.refs.name.value});
        $.ajax({
            type: 'POST',
            url: '/api/apps',
            contentType: 'application/json',
            data: data
        }).done(function(data){
            me.setState({status: 'launched'});
        });
    }
});

Home = connect(function(state) {
    return {auth: state.auth}
})(Home);

module.exports = {Home: Home, Overview: Overview, Hosts: Hosts, Apps: Apps};
