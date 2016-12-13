var React = require('react');
var connect = require('react-redux').connect;
var Network = require('../network');
var Bootstrap = require('react-bootstrap');

var Appp = React.createClass({
    getInitialState: function () {
        return {status: 'none', progress: 0, hosts: [], states: [], hostname: "", role: "", defaults: {sizes: [], networks: [], images: []}, stats: {cpu: "", maxCpu: "", ram: "", instances: ""}};
    },

    componentDidMount: function () {
        var me = this;
        Network.get('/api/hosts', this.props.auth.token).done(function (data) {
            me.setState({hosts: data.hosts});
            var host = {hostname: data.hosts[0].hostname};
            me.setState(host);
            if(data.hosts.length > 0){
                me.setState({defaults: {sizes: data.hosts[0].sizes, networks: data.hosts[0].networks, images: data.hosts[0].images}});
            }
            Network.post('/api/hosts/info', me.props.auth.token, host).done(function(data) {
                if(data){
                    var stats = data.limits.absolute;
                    me.setState({stats: {cpu: stats.totalCoresUsed, maxCpu: stats.maxTotalCores, ram: stats.totalRamUsed, instances: stats.totalInstancesUsed}});
                }
            });
        });
        Network.get('/api/states', this.props.auth.token).done(function (data) {
            me.setState({states: data});
            if(me.props.apps.select){
                me.setState({role: me.props.apps.select});
            }else{
                me.setState({role: data[0].name});
            }
        });
    },

    onChange: function(e) {
        value = e.target.value;
        var data = {hostname: e.target.value};
        this.setState(data);
        for(i=0; i < this.state.hosts.length; i++){
            var host = this.state.hosts[i];
            if(host.name === value){
                this.setState({defaults: {sizes: host.sizes, networks: host.networks, images: host.images}});
                break;
            }
        }
        Network.post('/api/hosts/info', this.props.auth.token, data).done(function(data) {
            if(data){
                var stats = data.limits.absolute;
                this.setState({stats: {cpu: stats.totalCoresUsed, maxCpu: stats.maxTotalCores, ram: stats.totalRamUsed, instances: stats.totalInstancesUsed}});
            }
        }.bind(this));
    },

    onChangeRole: function(e) {
        this.setState({role: e.target.value});
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
            if(state.name == this.props.apps.select){
                return <option key = {state.name} selected>{state.name}</option>
            }else{
                return <option key = {state.name}>{state.name}</option>
            }
        }.bind(this));

        var img_rows = this.state.defaults.images.map(function(img) {
            return <option key = {img}>{img}</option>
        });

        var sizes_rows = this.state.defaults.sizes.map(function(size) {
            return <option key = {size}>{size}</option>
        });

        var network_rows = this.state.defaults.networks.map(function(network) {
            return <option key = {network}>{network}</option>
        });

        var StatsRedux = connect(function(state){
            return {auth: state.auth};
        })(Stats);

        return (
            <div>
                <div className="forma">
                    <Bootstrap.PageHeader>Launch new app</Bootstrap.PageHeader>
                    <Bootstrap.Form onSubmit={this.onSubmit} horizontal>
                        <Bootstrap.FormGroup>
                            <Bootstrap.Col sm={4}>
                                <Bootstrap.FormControl componentClass="select" ref='role' onChange={this.onChangeRole}>
                                    {state_rows}
                                </Bootstrap.FormControl>
                            </Bootstrap.Col>
                            <Bootstrap.Col sm={8}>
                                <Bootstrap.FormControl type="text" ref='name' placeholder='Instance name' />
                            </Bootstrap.Col>
                        </Bootstrap.FormGroup>
                        <Bootstrap.FormGroup>
                            <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={2}>
                                Host
                            </Bootstrap.Col>
                            <Bootstrap.Col sm={10}>
                                <Bootstrap.FormControl componentClass="select" ref='hostname' onChange={this.onChange}>
                                    {host_rows}
                                </Bootstrap.FormControl>
                            </Bootstrap.Col>
                        </Bootstrap.FormGroup>
                        <Bootstrap.FormGroup>
                            <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={2}>
                                Image
                            </Bootstrap.Col>
                            <Bootstrap.Col sm={10}>
                                <Bootstrap.FormControl componentClass="select" ref='image'>
                                    {img_rows}
                                </Bootstrap.FormControl>
                            </Bootstrap.Col>
                        </Bootstrap.FormGroup>
                        <Bootstrap.FormGroup>
                            <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={2}>
                                Flavors
                            </Bootstrap.Col>
                            <Bootstrap.Col sm={10}>
                                <Bootstrap.FormControl componentClass="select" ref='flavor'>
                                    {sizes_rows}
                                </Bootstrap.FormControl>
                            </Bootstrap.Col>
                        </Bootstrap.FormGroup>
                        <Bootstrap.FormGroup>
                            <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={2}>
                                Storage disk
                            </Bootstrap.Col>
                            <Bootstrap.Col sm={10}>
                                <Bootstrap.FormControl type="text" ref='storage' />
                            </Bootstrap.Col>
                        </Bootstrap.FormGroup>
                        <Bootstrap.FormGroup>
                            <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={2}>
                                Networks
                            </Bootstrap.Col>
                            <Bootstrap.Col sm={10}>
                                <Bootstrap.FormControl componentClass="select" ref='network'>
                                    {network_rows}
                                </Bootstrap.FormControl>
                            </Bootstrap.Col>
                        </Bootstrap.FormGroup>
                        <Bootstrap.ButtonGroup>
                            <Bootstrap.Button type="submit" bsStyle='primary'>
                                Launch
                            </Bootstrap.Button>
                        </Bootstrap.ButtonGroup>
                        <div style={{width: '100%', padding: 10, borderRadius: 5, background: statusColor, display: statusDisplay}}>
                            {statusMessage}
                        </div>
                    </Bootstrap.Form>
                </div>
                <StatsRedux hostname = {this.state.hostname} stats = {this.state.stats} />
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
        var data = {instance_name: this.refs.name.value, hostname: this.refs.hostname.value, role: this.refs.role.value, size: this.refs.flavor.value, image: this.refs.image.value, storage: this.refs.storage.value, network: this.refs.network.value};
        Network.post('/api/apps', this.props.auth.token, data).done(function(data) {
            me.setState({status: 'launched'});
        });
    }
});

var Stats = React.createClass({
    render: function () {
        return (
            <div className="stats">
                <Bootstrap.PageHeader>{this.props.hostname}</Bootstrap.PageHeader>
                <label>CPU: </label>{this.props.stats.cpu} / {this.props.stats.maxCpu}<br/>
                <label>RAM: </label>{this.props.stats.ram}<br/>
                <label>INSTANCES: </label>{this.props.stats.instances}<br/>
            </div>
        );

    }
});

Apps = connect(function(state){
    return {auth: state.auth, apps: state.apps};
})(Appp);

module.exports = Apps;
