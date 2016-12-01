var React = require('react');
var connect = require('react-redux').connect;
var Network = require('../network');

var Apps = React.createClass({
    getInitialState: function () {
        return {status: 'none', progress: 0, hosts: [], states: [], sizes: [], networks: []};
    },

    componentDidMount: function () {
        var me = this;
        Network.get('/api/hosts', this.props.auth.token).done(function (data) {
            me.setState({hosts: data.hosts});
            if(data.hosts.length > 0){
                me.setState({sizes: data.hosts[0].sizes});
                me.setState({networks: data.hosts[0].networks});
            }
        });
        Network.get('/api/states', this.props.auth.token).done(function (data) {
            me.setState({states: data});
        });
    },

    onChange: function(e) {
        value = e.target.value;
        for(i=0; i < this.state.hosts.length; i++){
            var host = this.state.hosts[i];
            if(host.hostname === value){
                this.setState({sizes: host.sizes});
                this.setState({networks: host.networks});
                break;
            }
        }
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

        var host_rows = this.state.hosts.map(function(host, i) {
            return <option key = {i}>{host.hostname}</option>
        });

        var state_rows = this.state.states.map(function(state) {
            return <option key = {state.name}>{state.name}</option>
        });

        var sizes_rows = this.state.sizes.map(function(size) {
            return <option key = {size}>{size}</option>
        });

        var network_rows = this.state.networks.map(function(network) {
            return <option key = {network}>{network}</option>
        });

        return (
            <div>
                <h1>Launch new app</h1>
                <form onSubmit={this.onSubmit} className='form-horizontal'>
                    <div className='form-group'>
                    Host: <select ref='hostname' onChange={this.onChange}>
                        {host_rows}
                    </select> <br/>
                    <select ref = 'role'>
                        {state_rows}
                    </select>
                    <input placeholder='Instance name' ref='name'/> <br/>
                    Flavors: <select ref = 'flavor'>
                        {sizes_rows}
                    </select><br/>
                    Storage disk: <select ref = 'storage'>
                        <option>0</option>
                        <option>1</option>
                        <option>2</option>
                        <option>3</option>
                    </select><br/>
                    Networks: <select ref = 'network'>
                        {network_rows}
                    </select><br/>
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
        var data = {minion_name: this.refs.name.value, hostname: this.refs.hostname.value, role: this.refs.role.value};
        Network.post('/api/apps', this.props.auth.token, data).done(function(data) {
            me.setState({status: 'launched'});
        });
    }
});

Apps = connect(function(state){
    return {auth: state.auth};
})(Apps);

module.exports = Apps;
