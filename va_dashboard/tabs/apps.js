var React = require('react');
var connect = require('react-redux').connect;
var Network = require('../network');
var Bootstrap = require('react-bootstrap');
var ReactDOM = require('react-dom');
var Reactable = require('reactable');

var Appp = React.createClass({
    getInitialState: function () {
        return {
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
            var states = {};
            for(var i=0; i<resp3.length; i++){
                var state = resp3[i];
                states[state.name] = [];
                if("fields" in state){
                    states[state.name] = state.fields;
                }
            }
            me.setState({host_usage: host_usage, hosts: hosts, hostname: first_host.hostname, options: {sizes: first_host.sizes, networks: first_host.networks, images: first_host.images, sec_groups: first_host.sec_groups}, defaults: first_host.defaults, states: states, role: role, loaded: true});
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
                var rowClass = "row-app-" + app.status;
                return (
                    <Reactable.Tr key={app.hostname} className={rowClass}>
                        <Reactable.Td column="Hostname">{app.hostname}</Reactable.Td>
                        <Reactable.Td column="IP">{ipaddr}</Reactable.Td>
                        <Reactable.Td column="Size">{app.size}</Reactable.Td>
                        <Reactable.Td column="Status">{app.status}</Reactable.Td>
                        <Reactable.Td column="Host">{app.host}</Reactable.Td>
                        <Reactable.Td column="Actions">
                            <Bootstrap.DropdownButton id={'dropdown-' + app.hostname} bsStyle='primary' title="Choose" onSelect = {this.btn_clicked.bind(this, app.hostname, app.host)}>
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
        var sf_cols = ['Hostname', 'IP', 'Size', 'Status', 'Host'];

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
                    <Reactable.Table className="table striped" columns={['Hostname', 'IP', 'Size', 'Status', 'Host', 'Actions']} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={sf_cols} filterable={sf_cols} >
                        {app_rows}
                    </Reactable.Table>
                </div>
            </div>
        );
    }
});

var UserStep = React.createClass({
    getInitialState: function () {
        var fields = this.props.fields.map(function(field) {
            return field.name;
        });
        return {user: 'new', fields: fields};
    },

    radioChange: function (evt) {
        this.setState({user: evt.target.value});
    },

    render: function () {
        var me = this;

        var fields = null;

        if(this.state.user === "existing"){
            fields = this.props.fields.map(function(field, i) {
                return (
                    <Bootstrap.FormGroup key={field.name}>
                        <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                            {field.label}
                        </Bootstrap.Col>
                        <Bootstrap.Col sm={9}>
                            <Bootstrap.FormControl type={field.type} ref={field.name} />
                        </Bootstrap.Col>
                    </Bootstrap.FormGroup>
                );
            });
        }

        return (
            <Bootstrap.Form ref="form" horizontal>
                <div className="radioGroup">
                    <input type="radio" value="new" name="user" checked={this.state.user === "new"} onChange={this.radioChange} /> New user
                    <input type="radio" value="existing" name="user" checked={this.state.user === "existing"} onChange={this.radioChange} /> Join to existing
                </div>
                {fields}
            </Bootstrap.Form>
        );
    },
    onSubmit: function() {
        //e.preventDefault();
        var me = this;
        var type_user = this.state.user;
        if(type_user === "existing"){
            var data = {'step': 2};
            for(var i=0; i<this.state.fields.length; i++){
                field = this.state.fields[i];
                data[field] = ReactDOM.findDOMNode(this.refs[field]).value;
            }
            Network.post('/api/apps/new/validate_fields', this.props.auth.token, data).done(function(data) {
                me.props.goToNextStep();
            }).fail(function (msg) {
                me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            });
        }else{
            this.props.goToNextStep();
        }
    }

});

var HostStep = React.createClass({
    getInitialState: function () {
        return {progress: 0, hostname: this.props.hostname, options: this.props.options, defaults: this.props.defaults, index: 0};
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

    render: function () {
        var statusColor, statusDisplay, statusMessage;

        if(this.props.status == 'launching'){
            statusColor = 'yellow';
            statusDisplay = 'block';
            statusMessage = 'Launching... ' + this.state.progress + '%';
        }else if(this.props.status == 'launched'){
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

        var img_rows = this.state.options.images.map(function(img) {
            return <option key = {img}>{img}</option>
        });

        var sizes_rows = this.state.options.sizes.map(function(size) {
            return <option key = {size}>{size}</option>
        });

        var network_rows = this.state.options.networks.map(function(network) {
            return <option key = {network.split("|")[1]}>{network}</option>
        });

        var sec_groups = this.state.options.sec_groups.map(function(sec) {
            return <option key = {sec.split("|")[1]}>{sec}</option>
        });

        var StatsRedux = connect(function(state){
            return {auth: state.auth};
        })(Stats);

        return (
            <div>
                <Bootstrap.Col xs={12} sm={7} md={7} className="app-column">
                    <Bootstrap.Form ref="form" horizontal>
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
                                <Bootstrap.FormControl componentClass="select" ref='image' defaultValue={this.state.defaults.image}>
                                    {img_rows}
                                </Bootstrap.FormControl>
                            </Bootstrap.Col>
                        </Bootstrap.FormGroup>
                        <Bootstrap.FormGroup>
                            <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                                Flavors
                            </Bootstrap.Col>
                            <Bootstrap.Col sm={9}>
                                <Bootstrap.FormControl componentClass="select" ref='flavor' defaultValue={this.state.defaults.size}>
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
                                <Bootstrap.FormControl componentClass="select" ref='network' defaultValue={this.props.defaults.network}>
                                    {network_rows}
                                </Bootstrap.FormControl>
                            </Bootstrap.Col>
                        </Bootstrap.FormGroup>
                        <Bootstrap.FormGroup>
                            <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                                Security group
                            </Bootstrap.Col>
                            <Bootstrap.Col sm={9}>
                                <Bootstrap.FormControl componentClass="select" ref='sec_group' defaultValue={this.props.defaults.sec_group}>
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
                        <div style={{width: '100%', padding: 10, borderRadius: 5, background: statusColor, display: statusDisplay}}>
                            {statusMessage}
                        </div>
                    </Bootstrap.Form>
                </Bootstrap.Col>
                <StatsRedux hostname = {this.state.hostname} host_usage = {this.props.host_usage[this.state.index]} />
            </div>
        );
    },
    onSubmit: function() {
        //e.preventDefault();
        var me = this;
        this.setState({progress: 0});
        interval = setInterval(function(){
            if(me.props.status == 'launching' && me.state.progress <= 80){
                var newProgress = me.state.progress + 10;
                me.setState({progress: newProgress})
            }else{
                clearInterval(interval);
            }
        }, 10000);
        var data = {
            step: 3,
            hostname: ReactDOM.findDOMNode(this.refs.hostname).value,
            size: ReactDOM.findDOMNode(this.refs.flavor).value,
            image: ReactDOM.findDOMNode(this.refs.image).value,
            storage: ReactDOM.findDOMNode(this.refs.storage).value,
            network: ReactDOM.findDOMNode(this.refs.network).value,
            sec_group: ReactDOM.findDOMNode(this.refs.sec_group).value,
            username: ReactDOM.findDOMNode(this.refs.username).value
        };
        Network.post('/api/apps/new/validate_fields', this.props.auth.token, data).done(function(data) {
            //me.setState({status: 'launched'});
            me.props.launchApp();
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }

});

var AppForm = React.createClass({
    getInitialState: function () {
        return {role: this.props.role, step2: false, stepIndex: 1, isLoading: false, errors: [], instance_name: "", status: 'none', btnDisable: false};
    },

    onChangeRole: function(e) {
        this.setState({role: e.target.value, step2: this.props.states[e.target.value].length > 0});
    },

    close: function() {
        this.props.dispatch({type: 'CLOSE_MODAL'});
        this.setState({stepIndex: 1});
    },

    goToNextStep: function () {
        this.setState({stepIndex: 3});
    },

    launchApp: function () {
        //this.close();
        this.setState({btnDisable: true, status: 'launched'});
    },

    nextStep: function () {
        if(this.state.stepIndex === 1){
            var nextStep = this.state.step2 ? 2 : 3;
            var me = this, instance_name = ReactDOM.findDOMNode(this.refs.name).value;
            var data = {step: 1, role: ReactDOM.findDOMNode(this.refs.role).value, instance_name: instance_name};
            Network.post('/api/apps/new/validate_fields', this.props.auth.token, data).done(function(d) {
                me.setState({stepIndex: nextStep, instance_name: instance_name});
            }).fail(function (msg) {
                me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            });
        } else {
            // me.setState({isLoading: true});
            var stepIndex = this.state.stepIndex;
            var step_name = "step" + stepIndex;
            if(stepIndex === 3) this.setState({status: 'launching'});
            this.refs[step_name].getWrappedInstance().onSubmit();
            //this.setState({stepIndex: nextStep});
        }
    },

    render: function () {
        var me = this;

        var UserStepRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        }, null, null, { withRef: true })(UserStep);
        var HostStepRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        }, null, null, { withRef: true })(HostStep);

        var state_rows = Object.keys(this.props.states).map(function(state) {
            return <option key = {state}>{state}</option>
        });

        var step2 = null;
        if(this.state.step2){
            step2 = (
                <Bootstrap.Tab title='Choose user' eventKey={2}>
                    <UserStepRedux fields = {this.props.states[this.state.role]} goToNextStep = {this.goToNextStep} ref="step2" instance_name = {this.state.instance_name} />
                </Bootstrap.Tab>
            );
        }


        return (
            <Bootstrap.Modal show={this.props.modal.isOpen} onHide={this.close}>
                <Bootstrap.Modal.Header closeButton>
                  <Bootstrap.Modal.Title>Launch new app</Bootstrap.Modal.Title>
                </Bootstrap.Modal.Header>

                <Bootstrap.Modal.Body>
                    <Bootstrap.Tabs id="launch-app" activeKey={this.state.stepIndex}>
                        <Bootstrap.Tab title='Choose role' eventKey={1}>
                            <Bootstrap.Form onSubmit={this.onSubmit} horizontal>
                                <Bootstrap.FormGroup>
                                    <Bootstrap.Col sm={4}>
                                        <Bootstrap.FormControl componentClass="select" ref='role' defaultValue={this.props.apps.select} onChange={this.onChangeRole}>
                                            {state_rows}
                                        </Bootstrap.FormControl>
                                    </Bootstrap.Col>
                                    <Bootstrap.Col sm={8}>
                                        <Bootstrap.FormControl type="text" ref='name' placeholder='Instance name' />
                                    </Bootstrap.Col>
                                </Bootstrap.FormGroup>
                            </Bootstrap.Form>
                        </Bootstrap.Tab>

                        {step2}

                        <Bootstrap.Tab title='Choose host' eventKey={3}>
                            <HostStepRedux hostname = {this.props.hostname} hosts = {this.props.hosts} host_usage = {this.props.host_usage} options = {this.props.options} defaults = {this.props.defaults} ref="step3" changeStep = {this.changeStep} instance_name = {this.state.instance_name} status = {this.state.status}  launchApp = {this.launchApp} />
                        </Bootstrap.Tab>
                    </Bootstrap.Tabs>
                </Bootstrap.Modal.Body>

                <Bootstrap.Modal.Footer>
                    <Bootstrap.ButtonGroup>
                        <Bootstrap.Button disabled={this.state.isLoading || this.state.btnDisable} bsStyle='primary' onClick={this.nextStep}>
                            <Bootstrap.Glyphicon glyph='menu-right'></Bootstrap.Glyphicon> Next step</Bootstrap.Button>
                    </Bootstrap.ButtonGroup>
                </Bootstrap.Modal.Footer>
            </Bootstrap.Modal>
        );
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
