var React = require('react');
var connect = require('react-redux').connect;
var Network = require('../network');
var Bootstrap = require('react-bootstrap');
var ReactDOM = require('react-dom');
var Reactable = require('reactable');

var Appp = React.createClass({
    getInitialState: function () {
        return {host_info: [],
            loaded: false,
            hosts: [],
            states: [],
            hostname: "",
            role: "",
            defaults: {image: "", network: "", sec_group: "", size: ""},
            options: {sizes: [], networks: [], images: [], sec_groups: []},
            host_usage: [{used_cpus: "", max_cpus: "", used_ram: "", max_ram: "", used_disk: "", max_disk: "", used_instances: "", max_instances: ""}]
        };
    },

    getData: function() {
        var data = {hosts: []};
        var me = this;
        var n1 = Network.post('/api/hosts/info', this.props.auth.token, data).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
        var n2 = Network.post('/api/hosts', this.props.auth.token, {}).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
        var n3 = Network.get('/api/states', this.props.auth.token).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });

        $.when( n1, n2, n3 ).done(function ( resp1, resp2, resp3 ) {
            var host_usage = resp1.map(function(host) {
                return host.host_usage;
            });
            var hosts = resp2.hosts;
            var first_host = hosts[0];
            var role = resp3[0].name;
            if(me.props.apps.select){
                role = me.props.apps.select;
            }
            me.setState({host_info: resp1, host_usage: host_usage, hosts: hosts, hostname: first_host.hostname, options: {sizes: first_host.sizes, networks: first_host.networks, images: first_host.images, sec_groups: first_host.sec_groups}, defaults: first_host.defaults, states: resp3, role: role, loaded: true});
        });
    },

    componentDidMount: function () {
        this.getData();
    },

    componentWillUnmount: function () {
        this.props.dispatch({type: 'RESET_APP'});
    },

    btn_clicked: function(hostname, host, evtKey){
        var me = this;
        var data = {hostname: host, instance_name: hostname, action: evtKey};
        Network.post('/api/apps/action', this.props.auth.token, data).done(function(d) {
            Network.post('/api/hosts/info', me.props.auth.token, {hosts: []}).done(function(data) {
                me.setState({hosts: data});
            }).fail(function (msg) {
                me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            });
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },

    openModal: function () {
        this.props.dispatch({type: 'OPEN_MODAL'});
    },

    render: function () {
        var app_rows = [];
        for(var i = 0; i < this.state.hosts.length; i++){
            // hostname = this.state.hosts[i].hostname;
            var rows = this.state.hosts[i].instances.map(function(app) {
                ipaddr = app.ip;
                if(Array.isArray(ipaddr)){
                    if(ipaddr.length > 0){
                        var ips = "";
                        for(j=0; j<ipaddr.length; j++){
                            ips += ipaddr[j].addr + ", ";
                        }
                        ipaddr = ips.slice(0, -2);
                    }else{
                        ipaddr = "";
                    }
                }
                return (
                    <Reactable.Tr key={app.hostname}>
                        <Reactable.Td column="Hostname">{app.hostname}</Reactable.Td>
                        <Reactable.Td column="IP">{ipaddr}</Reactable.Td>
                        <Reactable.Td column="Size">{app.size}</Reactable.Td>
                        <Reactable.Td column="Status">{app.status}</Reactable.Td>
                        <Reactable.Td column="Host">{app.host}</Reactable.Td>
                        <Reactable.Td column="Actions">
                            <Bootstrap.DropdownButton bsStyle='primary' title="Choose" onSelect = {this.btn_clicked.bind(this, app.hostname, app.host)}>
                                <Bootstrap.MenuItem eventKey="reboot">Reboot</Bootstrap.MenuItem>
                                <Bootstrap.MenuItem eventKey="delete">Delete</Bootstrap.MenuItem>
                                <Bootstrap.MenuItem eventKey="start">Start</Bootstrap.MenuItem>
                                <Bootstrap.MenuItem eventKey="stop">Stop</Bootstrap.MenuItem>
                            </Bootstrap.DropdownButton>
                        </Reactable.Td>
                    </Reactable.Tr>
                );
            }.bind(this));
            app_rows.push(rows);
        }

        var AppFormRedux = connect(function(state){
            return {auth: state.auth, apps: state.apps, alert: state.alert, modal: state.modal};
        })(AppForm);

        var loaded = this.state.loaded;
        const spinnerStyle = {
            display: loaded ? "none": "block",
        };
        const blockStyle = {
            visibility: loaded ? "visible": "hidden",
        };

        return (
            <div className="app-containter">
                <span className="spinner" style={spinnerStyle} ><i className="fa fa-spinner fa-spin fa-3x"></i></span>
                <div style={blockStyle}>
                    <AppFormRedux hosts = {this.state.hosts} states = {this.state.states} hostname = {this.state.hostname} role = {this.state.role} defaults = {this.state.defaults} options = {this.state.options} host_usage = {this.state.host_usage} getData = {this.getData} onChange = {this.onChange} onChangeRole = {this.onChangeRole} />
                    <Bootstrap.PageHeader>Current apps <small>All specified apps</small></Bootstrap.PageHeader>
                    <Bootstrap.Button onClick={this.openModal} className="tbl-btn">
                        <Bootstrap.Glyphicon glyph='plus' />
                        Launch new app
                    </Bootstrap.Button>
                    <Reactable.Table className="table striped" columns={['Hostname', 'IP', 'Size', 'Status', 'Host', 'Actions']} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={['Hostname', 'IP', 'Size', 'Status', 'Host']} >
                        {app_rows}
                    </Reactable.Table>
                </div>
            </div>
        );
    }
});

var AppForm = React.createClass({
    getInitialState: function () {
        return {status: 'none', progress: 0, hostname: this.props.hostname, options: this.props.options, defaults: this.props.defaults, role: this.props.role, index: 0};
    },

    onChange: function(e) {
        var value = e.target.value;
        for(var i=0; i < this.props.hosts.length; i++){
            var host = this.props.hosts[i];
            if(host.hostname === value){
                this.setState({hostname: value, options: {sizes: host.sizes, networks: host.networks, images: host.images, sec_groups: host.sec_groups}, defaults: host.defaults, index: i});
                break;
            }
        }
    },

    onChangeRole: function(e) {
        this.setState({role: e.target.value});
    },

    close: function() {
        this.props.dispatch({type: 'CLOSE_MODAL'});
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

        var me = this;

        var host_rows = this.props.hosts.map(function(host, i) {
            return <option key = {i}>{host.hostname}</option>
        });

        var state_rows = this.props.states.map(function(state) {
            if(state.name == me.props.apps.select){
                return <option key = {state.name} selected>{state.name}</option>
            }else{
                return <option key = {state.name}>{state.name}</option>
            }
        });

        var img_rows = this.state.options.images.map(function(img) {
            if(img == me.state.defaults.image){
                return <option key = {img} selected>{img}</option>
            }
            return <option key = {img}>{img}</option>
        });

        var sizes_rows = this.state.options.sizes.map(function(size) {
            if(size == me.state.defaults.size){
                return <option key = {size} selected>{size}</option>
            }
            return <option key = {size}>{size}</option>
        });

        var network_rows = this.state.options.networks.map(function(network) {
            if(network.split("|")[1] == me.props.defaults.network){
                return <option key = {network} selected>{network}</option>
            }
            return <option key = {network}>{network}</option>
        });

        var sec_groups = this.state.options.sec_groups.map(function(sec) {
            if(sec.split("|")[1] == me.state.defaults.sec_group){
                return <option key = {sec} selected>{sec}</option>
            }
            return <option key = {sec}>{sec}</option>
        });

        var StatsRedux = connect(function(state){
            return {auth: state.auth};
        })(Stats);

        return (
            <Bootstrap.Modal show={this.props.modal.isOpen} onHide={this.close}>
                <Bootstrap.Modal.Header closeButton>
                  <Bootstrap.Modal.Title>Launch new app</Bootstrap.Modal.Title>
                </Bootstrap.Modal.Header>

                <Bootstrap.Modal.Body>
                    <Bootstrap.Col xs={12} sm={7} md={7} className="app-column">
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
                                <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                                    Host
                                </Bootstrap.Col>
                                <Bootstrap.Col sm={9}>
                                    <Bootstrap.FormControl componentClass="select" ref='hostname' onChange={this.onChange}>
                                        {host_rows}
                                    </Bootstrap.FormControl>
                                </Bootstrap.Col>
                            </Bootstrap.FormGroup>
                            <Bootstrap.FormGroup>
                                <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                                    Image
                                </Bootstrap.Col>
                                <Bootstrap.Col sm={9}>
                                    <Bootstrap.FormControl componentClass="select" ref='image'>
                                        {img_rows}
                                    </Bootstrap.FormControl>
                                </Bootstrap.Col>
                            </Bootstrap.FormGroup>
                            <Bootstrap.FormGroup>
                                <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                                    Flavors
                                </Bootstrap.Col>
                                <Bootstrap.Col sm={9}>
                                    <Bootstrap.FormControl componentClass="select" ref='flavor'>
                                        {sizes_rows}
                                    </Bootstrap.FormControl>
                                </Bootstrap.Col>
                            </Bootstrap.FormGroup>
                            <Bootstrap.FormGroup>
                                <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                                    Storage disk
                                </Bootstrap.Col>
                                <Bootstrap.Col sm={9}>
                                    <Bootstrap.FormControl type="text" ref='storage' />
                                </Bootstrap.Col>
                            </Bootstrap.FormGroup>
                            <Bootstrap.FormGroup>
                                <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                                    Networks
                                </Bootstrap.Col>
                                <Bootstrap.Col sm={9}>
                                    <Bootstrap.FormControl componentClass="select" ref='network'>
                                        {network_rows}
                                    </Bootstrap.FormControl>
                                </Bootstrap.Col>
                            </Bootstrap.FormGroup>
                            <Bootstrap.FormGroup>
                                <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                                    Security group
                                </Bootstrap.Col>
                                <Bootstrap.Col sm={9}>
                                    <Bootstrap.FormControl componentClass="select" ref='sec_group'>
                                        {sec_groups}
                                    </Bootstrap.FormControl>
                                </Bootstrap.Col>
                            </Bootstrap.FormGroup>
                            <Bootstrap.FormGroup>
                                <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                                    Login as user
                                </Bootstrap.Col>
                                <Bootstrap.Col sm={9}>
                                    <Bootstrap.FormControl type="text" ref='username' />
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
                    </Bootstrap.Col>
                    <StatsRedux hostname = {this.state.hostname} host_usage = {this.props.host_usage[this.state.index]} />
                </Bootstrap.Modal.Body>
            </Bootstrap.Modal>
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
        var data = {
            instance_name: ReactDOM.findDOMNode(this.refs.name).value,
            hostname: ReactDOM.findDOMNode(this.refs.hostname).value,
            role: ReactDOM.findDOMNode(this.refs.role).value,
            size: ReactDOM.findDOMNode(this.refs.flavor).value,
            image: ReactDOM.findDOMNode(this.refs.image).value,
            storage: ReactDOM.findDOMNode(this.refs.storage).value,
            network: ReactDOM.findDOMNode(this.refs.network).value,
            sec_group: ReactDOM.findDOMNode(this.refs.sec_group).value,
            username: ReactDOM.findDOMNode(this.refs.username).value
        };
        Network.post('/api/apps', this.props.auth.token, data).done(function(data) {
            setTimeout(function(){
                me.setState({status: 'launched'});
                me.props.getData();
            }, 2000);
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }
});

var Stats = React.createClass({
    render: function () {
        return (
            <Bootstrap.Col xs={12} sm={5} md={5}>
                <h3>{this.props.hostname}</h3>
                <label>CPU: </label>{this.props.host_usage.used_cpus} / {this.props.host_usage.max_cpus}<br/>
                <label>RAM: </label>{this.props.host_usage.used_ram} / {this.props.host_usage.max_ram}<br/>
                <label>DISK: </label>{this.props.host_usage.used_disk} / {this.props.host_usage.max_disk}<br/>
                <label>INSTANCES: </label>{this.props.host_usage.used_instances} / {this.props.host_usage.max_instances}<br/>
            </Bootstrap.Col>
        );

    }
});

Apps = connect(function(state){
    return {auth: state.auth, apps: state.apps, alert: state.alert};
})(Appp);

module.exports = Apps;
