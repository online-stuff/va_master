var React = require('react');
var connect = require('react-redux').connect;
var Network = require('../network');
var Bootstrap = require('react-bootstrap');

var Apps = React.createClass({
    getInitialState: function () {
        return {status: 'none', progress: 0, hosts: [], states: [], sizes: [], networks: [], images: []};
    },

    componentDidMount: function () {
        var me = this;
        Network.get('/api/hosts', this.props.auth.token).done(function (data) {
            me.setState({hosts: data.hosts});
            if(data.hosts.length > 0){
                me.setState({sizes: data.hosts[0].sizes});
                me.setState({networks: data.hosts[0].networks});
                me.setState({images: data.hosts[0].images});
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
                this.setState({images: host.images});
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

        var img_rows = this.state.images.map(function(img) {
            return <option key = {img}>{img}</option>
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
                <Bootstrap.Form onSubmit={this.onSubmit} horizontal className="forma">
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
                        <Bootstrap.Col sm={4}>
                            <Bootstrap.FormControl componentClass="select" ref='role'>
                                {state_rows}
                            </Bootstrap.FormControl>
                        </Bootstrap.Col>
                        <Bootstrap.Col sm={8}>
                            <Bootstrap.FormControl type="text" ref='name' placeholder='Instance name' />
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

Apps = connect(function(state){
    return {auth: state.auth};
})(Apps);

module.exports = Apps;
