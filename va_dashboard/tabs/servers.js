import React, { Component } from 'react';
import { connect } from 'react-redux';
var Network = require('../network');
var Bootstrap = require('react-bootstrap');
import { findDOMNode } from 'react-dom';
import { Table, Tr, Td } from 'reactable';
import { ConfirmPopup } from './shared_components';

class Servers extends Component {
    constructor (props) {
        super(props);
        this.state = {
            loaded: false,
            providers: [],
            servers: [],
            states: [],
            provider_name: "",
            role: "",
            defaults: {image: "", network: "", sec_group: "", size: ""},
            options: {sizes: [], networks: [], images: [], sec_groups: []},
            provider_usage: [{used_cpus: "", max_cpus: "", used_ram: "", max_ram: "", used_disk: "", max_disk: "", used_servers: "", max_servers: ""}],
            popupShow: false,
            popupData: ['','','']
        };
        this.getData = this.getData.bind(this);
        this.btn_clicked = this.btn_clicked.bind(this);
        this.confirm_action = this.confirm_action.bind(this);
        this.popupClose = this.popupClose.bind(this);
        this.openModal = this.openModal.bind(this);
    }

    getData() {
        var data = {providers: []};
        var me = this;
        var n1 = Network.post('/api/providers/info', this.props.auth.token, data).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
        var n2 = Network.post('/api/providers', this.props.auth.token, {}).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
        var n3 = Network.get('/api/states', this.props.auth.token).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });

        $.when( n1, n2, n3 ).done(function ( resp1, resp2, resp3 ) {
            var provider_usage = resp1.map(function(provider) {
                return provider.provider_usage;
            });
            var providers = resp2.providers;
            if(providers.length > 0)
                var first_provider = providers[0];
            else
                first_provider = {provider_name: "", sizes: [], networks: [], images: [], sec_groups: [], defaults: []};
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
            me.setState({provider_usage: provider_usage, providers: providers, provider_name: first_provider.provider_name, options: {sizes: first_provider.sizes, networks: first_provider.networks, images: first_provider.images, sec_groups: first_provider.sec_groups}, defaults: first_provider.defaults, states: states, role: role, loaded: true, servers: resp1});
        });
    }

    componentDidMount() {
        this.getData();
    }

    componentWillUnmount () {
        this.props.dispatch({type: 'RESET_APP'});
    }

    btn_clicked(provider, server, evtKey){
        var me = this;
        var data = {provider_name: provider, server_name: server, action: evtKey};
        Network.post('/api/apps/action', this.props.auth.token, data).done(function(d) {
            Network.post('/api/providers/info', me.props.auth.token, {providers: []}).done(function(data) {
                me.setState({providers: data, popupShow: false});
            }).fail(function (msg) {
                me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            });
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }

    confirm_action(provider, server, evtKey){
        if(evtKey == 'reboot' || evtKey == 'delete')
            this.setState({popupShow: true, popupData: [provider, server, evtKey]});
        else
            this.btn_clicked(provider, server, evtKey);
    }

    popupClose() {
        this.setState({popupShow: false});
    }

    openModal () {
        this.props.dispatch({type: 'OPEN_MODAL'});
    }

    render () {
        var app_rows = [];
        for(var i = 0; i < this.state.servers.length; i++){
            // provider_name = this.state.providers[i].provider_name;
            var rows = this.state.servers[i].servers.map(function(app) {
                let ipaddr = app.ip;
                if(Array.isArray(ipaddr)){
                    if(ipaddr.length > 0){
                        var ips = ipaddr.join(", ");
                        ipaddr = ips.slice(0, -2);
                    }else{
                        ipaddr = "";
                    }
                }
                var rowClass = "row-app-" + app.status;
                return (
                    <Tr key={app.hostname} className={rowClass}>
                        <Td column="Hostname">{app.hostname}</Td>
                        <Td column="IP">{ipaddr}</Td>
                        <Td column="Size">{app.size}</Td>
                        <Td column="Status">{app.status}</Td>
                        <Td column="Provider">{app.provider}</Td>
                        <Td column="Actions">
                            <Bootstrap.DropdownButton id={'dropdown-' + app.hostname} bsStyle='primary' title="Choose" onSelect = {this.confirm_action.bind(null, app.provider, app.hostname)}>
                                <Bootstrap.MenuItem className="danger" eventKey="reboot">Reboot</Bootstrap.MenuItem>
                                <Bootstrap.MenuItem className="danger" eventKey="delete">Delete</Bootstrap.MenuItem>
                                <Bootstrap.MenuItem eventKey="start">Start</Bootstrap.MenuItem>
                                <Bootstrap.MenuItem eventKey="stop">Stop</Bootstrap.MenuItem>
                            </Bootstrap.DropdownButton>
                        </Td>
                    </Tr>
                );
            }.bind(this));
            app_rows.push(rows);
        }

        var ServerFormRedux = connect(function(state){
            return {auth: state.auth, apps: state.apps, alert: state.alert, modal: state.modal};
        })(ServerForm);

        var loaded = this.state.loaded;
        const spinnerStyle = {
            display: loaded ? "none": "block",
        };
        const blockStyle = {
            visibility: loaded ? "visible": "hidden",
        };
        var sf_cols = ['Hostname', 'IP', 'Size', 'Status', 'Host'];
        var popupData = this.state.popupData;

        return (
            <div className="app-containter">
                <span className="spinner" style={spinnerStyle} ><i className="fa fa-spinner fa-spin fa-3x"></i></span>
                <div style={blockStyle}>
                    <ServerFormRedux loaded={loaded} providers = {this.state.providers} states = {this.state.states} provider_name = {this.state.hostname} role = {this.state.role} defaults = {this.state.defaults} options = {this.state.options} provider_usage = {this.state.provider_usage} getData = {this.getData} onChange = {this.onChange} onChangeRole = {this.onChangeRole} />
                    <div style={blockStyle} className="card">
                        <div className="card-body">
                            <Table className="table striped" columns={['Hostname', 'IP', 'Size', 'Status', 'Provider', 'Actions']} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={sf_cols} filterable={sf_cols} btnName="Create server" btnClick={this.openModal} title="Current servers" filterClassName="form-control" filterPlaceholder="Filter">
                                {app_rows}
                            </Table>
                        </div>
                    </div>
                    <ConfirmPopup body={`Please confirm action: ${popupData[2]} server ${popupData[0]}`} show={this.state.popupShow} data={popupData} close={this.popupClose} action={this.btn_clicked} />
                </div>
            </div>
        );
    }
}

class UserStep extends Component {
    constructor (props) {
        super(props);
        var fields = this.props.fields.map(function(field) {
            return field.name;
        });
        this.state = {user: 'new', fields: fields};
        this.radioChange = this.radioChange.bind(this);
        this.onSubmit = this.onSubmit.bind(this);
    }

    radioChange (evt) {
        this.setState({user: evt.target.value});
    }

    render () {
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
            <form ref="form" className="form-horizontal">
                <div className="radioGroup">
                    <label className="radio-inline">
                        <input type="radio" value="new" name="user" checked={this.state.user === "new"} onChange={this.radioChange} /> New user
                    </label>
                    <label className="radio-inline">
                        <input type="radio" value="existing" name="user" checked={this.state.user === "existing"} onChange={this.radioChange} /> Join to existing
                    </label>
                </div>
                {fields}
            </form>
        );
    }
    onSubmit() {
        //e.preventDefault();
        var me = this;
        var type_user = this.state.user;
        if(type_user === "existing"){
            var data = {'step': 2};
            for(var i=0; i<this.state.fields.length; i++){
                field = this.state.fields[i];
                data[field] = findDOMNode(this.refs[field]).value;
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

}

class SSHStep extends Component {
    constructor (props) {
        super(props);
        this.state = {progress: 0, auth: false};
        this.toggleAuth = this.toggleAuth.bind(this);
        this.onSubmit = this.onSubmit.bind(this);
    }

    toggleAuth (e) {
        this.setState({auth: e.target.checked});
    }

    onSubmit() {
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
            ip: findDOMNode(this.refs.ip).value,
            port: findDOMNode(this.refs.port).value,
            hostname: findDOMNode(this.refs.hostname).value,
            username: findDOMNode(this.refs.username).value,
            location: findDOMNode(this.refs.location).value
        };
        if(!this.state.auth)
            data['password'] = findDOMNode(this.refs.password).value;
        Network.post('/api/apps/new/validate_fields', this.props.auth.token, data).done(function(data) {
            //me.setState({status: 'launched'});
            me.props.launchServer();
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }

    render () {
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

        return (
            <form ref="form" className="form-horizontal">
                <Bootstrap.FormGroup>
                    <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                        IP address
                    </Bootstrap.Col>
                    <Bootstrap.Col sm={9}>
                        <Bootstrap.FormControl type="text" ref='ip' />
                    </Bootstrap.Col>
                </Bootstrap.FormGroup>

                <Bootstrap.FormGroup>
                    <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                        Hostname
                    </Bootstrap.Col>
                    <Bootstrap.Col sm={9}>
                        <Bootstrap.FormControl type="text" ref='hostname' />
                    </Bootstrap.Col>
                </Bootstrap.FormGroup>

                <Bootstrap.FormGroup>
                    <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                        Location
                    </Bootstrap.Col>
                    <Bootstrap.Col sm={9}>
                        <Bootstrap.FormControl type="text" ref='location' />
                    </Bootstrap.Col>
                </Bootstrap.FormGroup>

                <Bootstrap.FormGroup>
                    <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                        SSH port
                    </Bootstrap.Col>
                    <Bootstrap.Col sm={9}>
                        <Bootstrap.FormControl type="number" ref='port' />
                    </Bootstrap.Col>
                </Bootstrap.FormGroup>

                <Bootstrap.FormGroup>
                    <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                        Username 
                    </Bootstrap.Col>
                    <Bootstrap.Col sm={9}>
                        <Bootstrap.FormControl type="text" ref='username' />
                    </Bootstrap.Col>
                </Bootstrap.FormGroup>
                
                <Bootstrap.FormGroup>
                    <div className="col-sm-offset-3 col-sm-9">
                        <div className="checkbox">
                            <label>
                                <input type="checkbox" onChange={this.toggleAuth} />
                                Use SSH Key Auth?
                            </label>
                        </div>
                    </div>
                </Bootstrap.FormGroup>

                {!this.state.auth && <Bootstrap.FormGroup>
                    <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                        Password 
                    </Bootstrap.Col>
                    <Bootstrap.Col sm={9}>
                        <Bootstrap.FormControl type="password" ref='password' />
                    </Bootstrap.Col>
                </Bootstrap.FormGroup>}
            </form>
        );
    }
}

class HostStep extends Component {
    constructor (props) {
        super(props);
        this.state = {progress: 0, provider_name: this.props.hostname, options: this.props.options, defaults: this.props.defaults, index: 0};
        this.onChange = this.onChange.bind(this);
        this.onSubmit = this.onSubmit.bind(this);
    }

    onChange(e) {
        var value = e.target.value;
        for(var i=0; i < this.props.providers.length; i++){
            var provider = this.props.providers[i];
            if(provider.provider_name === value){
                this.setState({provider_name: value, options: {sizes: provider.sizes, networks: provider.networks, images: provider.images, sec_groups: provider.sec_groups}, defaults: provider.defaults, index: i});
                break;
            }
        }
    }

    render () {
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

        var provider_rows = this.props.providers.map(function(provider, i) {
            return <option key = {i}>{provider.provider_name}</option>
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
                    <form ref="form" className="form-horizontal">
                        <Bootstrap.FormGroup>
                            <Bootstrap.Col componentClass={Bootstrap.ControlLabel} sm={3}>
                                Provider 
                            </Bootstrap.Col>
                            <Bootstrap.Col sm={9}>
                                <Bootstrap.FormControl componentClass="select" ref='provider_name' onChange={this.onChange}>
                                    {provider_rows}
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
                    </form>
                </Bootstrap.Col>
                <StatsRedux provider_name = {this.state.hostname} provider_usage = {this.props.provider_usage[this.state.index]} />
            </div>
        );
    }
    onSubmit() {
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
            provider_name: findDOMNode(this.refs.provider_name).value,
            size: findDOMNode(this.refs.flavor).value,
            image: findDOMNode(this.refs.image).value,
            storage: findDOMNode(this.refs.storage).value,
            network: findDOMNode(this.refs.network).value,
            sec_group: findDOMNode(this.refs.sec_group).value,
            username: findDOMNode(this.refs.username).value
        };
        Network.post('/api/apps/new/validate_fields', this.props.auth.token, data).done(function(data) {
            //me.setState({status: 'launched'});
            me.props.launchServer();
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }

}

class ServerForm extends Component {
    constructor (props) {
        super(props);
        var provider_name = "", standalone = true;
        if(this.props.providers.length > 0){
            provider_name = this.props.providers[0].provider_name;
            standalone = false;
        }
        this.state = {role: this.props.role, provider_name: provider_name, step2: false, standalone: standalone, stepIndex: 1, isLoading: false, errors: [], server_name: "", status: 'none', btnDisable: false};
        this.onChangeRole = this.onChangeRole.bind(this);
        this.onChangeProvider = this.onChangeProvider.bind(this);
        this.close = this.close.bind(this);
        this.goToNextStep = this.goToNextStep.bind(this);
        this.launchServer = this.launchServer.bind(this);
        this.nextStep = this.nextStep.bind(this);
        this.toggleStandalone = this.toggleStandalone.bind(this);
    }

    onChangeRole(e) {
        this.setState({role: e.target.value, step2: e.target.value && this.props.states[e.target.value].length > 0});
    }

    onChangeProvider(e){
        this.setState({provider_name: e.target.value});
    }

    close() {
        this.props.dispatch({type: 'CLOSE_MODAL'});
        this.setState({stepIndex: 1});
    }

    goToNextStep () {
        this.setState({stepIndex: 3});
    }

    launchServer () {
        //this.close();
        this.setState({btnDisable: true, status: 'launched'});
    }

    nextStep () {
        if(this.state.stepIndex === 1){
            var nextStep = this.state.step2 ? 2 : 3;
            var me = this, server_name = findDOMNode(this.refs.name).value;
            var data = {step: 1, role: findDOMNode(this.refs.role).value, server_name: server_name};
            if(!this.state.standalone)
                data.provider_name = this.state.provider_name;
            Network.post('/api/apps/new/validate_fields', this.props.auth.token, data).done(function(d) {
                me.setState({stepIndex: nextStep, server_name: server_name});
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
    }

    toggleStandalone (e) {
        this.setState({standalone: e.target.checked});
    }

    render () {
        var me = this;

        var UserStepRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        }, null, null, { withRef: true })(UserStep);
        var HostStepRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        }, null, null, { withRef: true })(HostStep);
        var SSHStepRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        }, null, null, { withRef: true })(SSHStep);

        var state_rows = Object.keys(this.props.states).map(function(state) {
            return <option key = {state}>{state}</option>
        });
        var provider_rows = this.props.providers.map(function(provider, i) {
            return <option key = {i}>{provider.provider_name}</option>
        });
        state_rows.push( <option key='-1' value=''>none</option> );

        var step2 = null, step3 = null;
        if(this.state.step2){
            step2 = (
                <Bootstrap.Tab title='Choose user' eventKey={2}>
                    <UserStepRedux fields = {this.props.states[this.state.role]} goToNextStep = {this.goToNextStep} ref="step2" server_name = {this.state.server_name} />
                </Bootstrap.Tab>
            );
        }
        if(this.state.standalone){
            step3 = (
                <Bootstrap.Tab title='Choose ssh' eventKey={3}>
                    <SSHStepRedux ref="step3" status = {this.state.status} launchServer = {this.launchServer} />
                </Bootstrap.Tab>
            );
        }else{
            step3 = (
                <Bootstrap.Tab title='Choose provider' eventKey={3}>
                    <HostStepRedux provider_name = {this.props.hostname} providers = {this.props.providers} provider_usage = {this.props.provider_usage} options = {this.props.options} defaults = {this.props.defaults} ref="step3" changeStep = {this.changeStep} server_name = {this.state.server_name} status = {this.state.status}  launchServer = {this.launchServer} />
                </Bootstrap.Tab>
            );
        }


        return (
            <Bootstrap.Modal show={this.props.loaded && this.props.modal.isOpen} onHide={this.close}>
                <Bootstrap.Modal.Header closeButton>
                  <Bootstrap.Modal.Title>Launch new app</Bootstrap.Modal.Title>
                </Bootstrap.Modal.Header>

                <Bootstrap.Modal.Body>
                    <Bootstrap.Tabs id="launch-app" activeKey={this.state.stepIndex}>
                        <Bootstrap.Tab title='Choose role' eventKey={1}>
                            <form className="form-horizontal">
                                <div className="form-group">
                                    <div className="col-sm-4">
                                        <select ref='role' className="form-control" defaultValue={this.props.apps.select} onChange={this.onChangeRole}>
                                            {state_rows}
                                        </select>
                                    </div>
                                    <div className="col-sm-8">
                                        <input type="text" ref='name' className="form-control" placeholder='Instance name' />
                                    </div>
                                </div>
                                {!this.state.standalone && <div className="form-group">
                                    <label htmlFor="provider-select" className="col-sm-4 control-label">Provider</label>
                                    <div className="col-sm-8">
                                        <select id="provider-select" className="form-control" defaultValue='-1' onChange={this.onChangeProvider.bind(this)}>
                                            {provider_rows}
                                        </select>
                                    </div>
                                </div>}
                                <div className="form-group">
                                    <div className="col-sm-12">
                                        <div className="checkbox" style={{paddingLeft: "15px"}}>
                                            <label>
                                                <input type="checkbox" defaultChecked={this.state.standalone} onChange={this.toggleStandalone} />
                                                Standalone?
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </form>
                        </Bootstrap.Tab>

                        {step2}
                        {step3}

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

}

const Stats = (props) => {
    return (
        <Bootstrap.Col xs={12} sm={5} md={5}>
            <h3>{props.provider_name}</h3>
            <label>CPU: </label>{props.provider_usage.used_cpus} / {props.provider_usage.max_cpus}<br/>
            <label>RAM: </label>{props.provider_usage.used_ram} / {props.provider_usage.max_ram}<br/>
            <label>DISK: </label>{props.provider_usage.used_disk} / {props.provider_usage.max_disk}<br/>
            <label>INSTANCES: </label>{props.provider_usage.used_servers} / {props.provider_usage.max_servers}<br/>
        </Bootstrap.Col>
    );
}

Servers = connect(function(state){
    return {auth: state.auth, apps: state.apps, alert: state.alert};
})(Servers);

module.exports = Servers;
