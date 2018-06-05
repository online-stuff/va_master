var React = require('react');
var Bootstrap = require('react-bootstrap');
var Network = require('../network');
var connect = require('react-redux').connect;
var ReactDOM = require('react-dom');

var Triggers = React.createClass({
    getInitialState: function () {
        return {triggers: [], operators: {'lt': '<', 'gt': '>', 'ge': '>=', 'le': '<='}, conditions: [], actions: [], icinga_status: ""};
    },
    getCurrentTriggers: function () {
        var me = this;
        Network.get('/api/triggers', this.props.auth.token).done(function (data) {
            var d = data["va-clc"];
            me.setState({triggers: d.triggers, conditions: d.functions.conditions, actions: d.functions.actions});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },
    componentDidMount: function () {
        this.getCurrentTriggers();
    },
    executeAction: function (rowId, evtKey) {
        switch (evtKey) {
            case "edit":
                var trigger = {};
                for(var i=0; i < this.state.triggers.length; i++){
                    if(this.state.triggers[i].id === rowId){
                        trigger = Object.assign({}, this.state.triggers[i]);
                        break;
                    }
                }
                this.props.dispatch({type: 'OPEN_MODAL', args: trigger, modalType: "EDIT"});
                break;
            case "delete":
                var data = {"hostname": "va-clc", "trigger_id": rowId}, me = this;
                Network.delete("/api/triggers/delete_trigger", this.props.auth.token, data).done(function(d) {
                    me.getCurrentTriggers();
                }).fail(function (msg) {
                    me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
                });
                break;
            default:
                break;
        }
    },
    openModal: function() {
        this.props.dispatch({type: 'OPEN_MODAL', modalType: "CREATE"});
    },
    addTrigger: function (t_data) {
        t_data.extra_kwargs = ["domain"];
        var me = this, data = {hostname: "va-clc", new_trigger: t_data};
        Network.post('/api/triggers/add_trigger', this.props.auth.token, data).done(function (data) {
            me.getCurrentTriggers();
            me.props.dispatch({type: 'CLOSE_MODAL'});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },
    editTrigger: function (id, t_data) {
        t_data.extra_kwargs = ["domain"];
        var me = this, data = {hostname: "va-clc", trigger_id: id, trigger: t_data};
        Network.post('/api/triggers/edit_trigger', this.props.auth.token, data).done(function (data) {
            var triggers = Object.assign([], me.state.triggers);
            for(var i=0; i < triggers.length; i++){
                if(triggers[i].id === id){
                    triggers[i] = {service: service, status: status, conditions: conditions, actions: actions, extra_kwargs: ["domain"], id: id};
                    break;
                }
            }
            me.setState({triggers: triggers});
            me.props.dispatch({type: 'CLOSE_MODAL'});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },
    updateTriggerVals: function (data) {
        var me = this;
        Network.post('/api/evo/change_icinga_services', this.props.auth.token, data).done(function (data) {
            me.setState({icinga_status: "Thresholds are updated."});

        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },
    render: function () {
        var me = this;
        var trigger_rows = this.state.triggers.map(function(trigger) {
            var conditions = trigger.conditions.map(function(c, j) {
                return (
                    <div key={j}>{c}</div>
                );
            });
            var actions = trigger.actions.map(function(a, j) {
                return (
                    <div key={j}>{a}</div>
                );
            });
            var actionBtn = (
                <Bootstrap.DropdownButton bsStyle='primary' title="Choose" onSelect = {me.executeAction.bind(me, trigger.id)}>
                    <Bootstrap.MenuItem key="edit" eventKey="edit">Edit</Bootstrap.MenuItem>
                    <Bootstrap.MenuItem key="delete" eventKey="delete">Delete</Bootstrap.MenuItem>
                </Bootstrap.DropdownButton>
            );
            return (
                <tr key={trigger.id}>
                    <td>{trigger.service}</td>
                    <td>{trigger.status}</td>
                    <td>{conditions}</td>
                    <td>Terminal</td>
                    <td>{actions}</td>
                    <td>{actionBtn}</td>
                </tr>
            );
        });
        var ModalRedux = connect(function(state){
            return {auth: state.auth, modal: state.modal, alert: state.alert};
        })(Modal);
        var TriggerFormRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        })(TriggerForm);

        return (
            <div>
                <TriggerFormRedux updateTriggerVals={this.updateTriggerVals} />
                <span id="action-status">{this.state.icinga_status}</span>
                <Bootstrap.PageHeader>List triggers</Bootstrap.PageHeader>
                <Bootstrap.Button type="button" bsStyle='default' className="pull-right margina" onClick={this.openModal}>
                    <Bootstrap.Glyphicon glyph='plus' />
                    Add trigger
                </Bootstrap.Button>
                <ModalRedux addTrigger = {this.addTrigger} editTrigger = {this.editTrigger} conditions = {this.state.conditions} actions = {this.state.actions} getCurrentTriggers = {this.getCurrentTriggers} />
                <Bootstrap.Table striped bordered hover>
                    <thead>
                        <tr>
                        <td>Service</td>
                        <td>Status</td>
                        <td>Conditions</td>
                        <td>Target</td>
                        <td>Actions</td>
                        <td></td>
                        </tr>
                    </thead>
                    <tbody>
                        {trigger_rows}
                    </tbody>
                </Bootstrap.Table>
            </div>
        );
    }
});

var Modal = React.createClass({
    getInitialState: function () {
        var values = {"service": "", "status": "", "conditions": "", "target": "", "actions": "", checkboxes: {}};
        var args = this.props.modal.args;
        if('service' in args){
            for(var key in args){
                values[key] = args[key];
            }
            var conditions = {}, actions = {};
            for(var i=0; i < args.conditions.length; i++){
                conditions[args.conditions[i]] = true;
            }
            for(var i=0; i < args.actions.length; i++){
                conditions[args.actions[i]] = true;
            }
            values.checkboxes = Object.assign({}, conditions, actions);
        }
        return values;
    },

    open: function() {
        this.props.dispatch({type: 'OPEN_MODAL'});
    },

    close: function() {
        this.props.dispatch({type: 'CLOSE_MODAL'});
    },

    toggleCheckbox: function(e) {
        var checkboxes = Object.assign({}, this.state.checkboxes);
        checkboxes[e.target.id] = !checkboxes[e.target.id]
        this.setState({checkboxes: checkboxes});
    },

    action: function(e) {
        console.log(e.target);
        console.log(this.refs.forma);
        console.log(ReactDOM.findDOMNode(this.refs.forma).elements);
        var elements = ReactDOM.findDOMNode(this.refs.forma).elements;
        var data = {conditions: [], actions: []};
        for(i=0; i<elements.length; i++){
            if(elements[i].name == "conditions" || elements[i].name == "actions") {
                if(this.state.checkboxes[elements[i].id])
                    data[elements[i].name].push(elements[i].id);
            }else{
                data[elements[i].name] = elements[i].value;
            }
        }
        console.log(data);
        if(this.props.modal.modalType === "CREATE"){
            this.props.addTrigger(data);
        }else{
            this.props.editTrigger(this.state.id, data);
        }
    },

    render: function () {
        var me = this;
        return (
            <Bootstrap.Modal show={this.props.modal.isOpen} onHide={this.close}>
            <Bootstrap.Modal.Header closeButton>
            <Bootstrap.Modal.Title>{this.props.modal.modalType === "CREATE" ? "Create Trigger" : "Edit Trigger"}</Bootstrap.Modal.Title>
            </Bootstrap.Modal.Header>

            <Bootstrap.Modal.Body>
                <div className="left">
                    <Bootstrap.Form ref="forma">
                        <Bootstrap.FormControl id="service" key="service" name="service" componentClass="select" defaultValue={this.state["service"]}>
                            <option value="CPU">CPU</option>
                            <option value="Memory">Memory</option>
                            <option value="CPUSize">CPUSize</option>
                            <option value="MemorySize">MemorySize</option>
                            <option value="Memory">Memory</option>
                        </Bootstrap.FormControl>
                        <Bootstrap.FormControl id="status" key="status" name="status" componentClass="select" defaultValue={this.state["status"]}>
                            <option value="CRITICAL">CRITICAL</option>
                            <option value="OK">OK</option>
                            <option value="WARNING">WARNING</option>
                        </Bootstrap.FormControl>
                        {this.props.conditions.map(function(option, i) {
                            return <Bootstrap.Checkbox id={option} key={option} name="conditions" onChange={me.toggleCheckbox} defaultChecked={me.state["conditions"].indexOf(option) > -1 ? true:false}>{option}</Bootstrap.Checkbox>
                        })}
                        <Bootstrap.FormControl type='text' name="target" value="Terminal" disabled />
                        {this.props.actions.map(function(option, i) {
                            return <Bootstrap.Checkbox id={option} key={option} name="actions" onChange={me.toggleCheckbox} defaultChecked={me.state["actions"].indexOf(option) > -1 ? true:false}>{option}</Bootstrap.Checkbox>
                        })}
                    </Bootstrap.Form>
                </div>
                <div className="right">
                    <h3>{this.props.modal.modalType === "CREATE" ? "Fill the form to add new trigger" : "Fill the form to edit existing trigger"}</h3>
                    <div></div>
                </div>
            </Bootstrap.Modal.Body>

            <Bootstrap.Modal.Footer>
            <Bootstrap.Button onClick={this.close}>Cancel</Bootstrap.Button>
            <Bootstrap.Button onClick={this.action} bsStyle = "primary">{this.props.modal.modalType === "CREATE" ? "Add trigger" : "Apply change"}</Bootstrap.Button>
            </Bootstrap.Modal.Footer>

        </Bootstrap.Modal>
        );
    }
});

var TriggerForm = React.createClass({
    getInitialState: function () {
        return {services: {CPU: {name: 'CPU', min: 50, max: 100, min_size: 2, max_size: 8, w_val: 0, c_val: 0, size: 0}, Memory: {name: 'Memory', min: 50, max: 100, min_size: 3000, max_size: 16000, w_val: 0, c_val: 0, size: 0}, TotalUsers: {name: 'Users', min: 0, max: 200, min_size: 50, max_size: 200, w_val: 0, c_val: 0, size: 0}}, severity: ['w_val', 'c_val', 'size']};
    },
    getTriggerVals: function () {
        var me = this;
        Network.get('/api/evo/get_all_icinga_services', this.props.auth.token).done(function (data) {
            var services = me.state.services;
            var cpu = Object.assign({}, services.CPU, data.CPU);
            var mem = Object.assign({}, services.Memory, data.Memory);
            var usr = Object.assign({}, services.TotalUsers, data.TotalUsers);
            me.setState({services: {CPU: cpu, Memory: mem, TotalUsers: usr}});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },
    componentDidMount: function () {
        this.getTriggerVals();
    },
    onChange: function(e) {
        var arr = e.target.id.split("_");
        var services = Object.assign({}, this.state.services);
        services[arr[0]][this.state.severity[arr[1]]] = e.target.value;
        this.setState({services: services});
    },
    updateTriggerVals: function (e) {
        e.preventDefault();
        var me = this;
        var data = [];
        for(var key in this.state.services){
            var service = this.state.services[key];
            data.push({service: key, severity : "WARNING", value: service.w_val});
            data.push({service: key, severity : "CRITICAL", value: service.c_val});
            data.push({service: key, severity : "MAXIMUM", value: service.size});
        }
        console.log(data);
        this.props.updateTriggerVals({services: data});
    },
    render: function () {
        var s = this.state.services;
        return (
            <div>
                <Bootstrap.PageHeader>Change thresholds</Bootstrap.PageHeader>
                <form onSubmit={this.updateTriggerVals}>
                    <table className="threshold-tbl">
                        <tr>
                            <th></th>
                            <th>Warning</th>
                            <th>Critical</th>
                            <th>Maximum</th>
                        </tr>
                        <tr>
                            <td>CPU</td>
                            <td><input type='number' min={s.CPU.min} max={s.CPU.max} id="CPU_0" key="CPU_0" value={s.CPU.w_val} onChange={this.onChange} /></td>
                            <td><input type='number' min={s.CPU.min < s.CPU.w_val ? s.CPU.w_val : s.CPU.min} max={s.CPU.max} id="CPU_1" key="CPU_1" value={s.CPU.c_val} onChange={this.onChange} /></td>
                            <td><input type='number' min={s.CPU.min_size} max={s.CPU.max_size} id="CPU_2" key="CPU_2" value={s.CPU.size} onChange={this.onChange} /></td>
                        </tr>
                        <tr>
                            <td>Memory</td>
                            <td><input type='number' min={s.Memory.min} max={s.Memory.max} id="Memory_0" key="Memory_0" value={s.Memory.w_val} onChange={this.onChange} /></td>
                            <td><input type='number' min={s.Memory.min < s.Memory.w_val ? s.Memory.w_val : s.Memory.min} max={s.Memory.max} id="Memory_1" key="Memory_1" value={s.Memory.c_val} onChange={this.onChange} /></td>
                            <td><input type='number' min={s.Memory.min_size} max={s.Memory.max_size} id="Memory_2" key="Memory_2" value={s.Memory.size} onChange={this.onChange} /></td>
                        </tr>
                        <tr>
                            <td>Users</td>
                            <td><input type='number' min={s.TotalUsers.min} max={s.TotalUsers.max} id="TotalUsers_0" key="TotalUsers_0" value={s.TotalUsers.w_val} onChange={this.onChange} /></td>
                            <td><input type='number' min={s.TotalUsers.min < s.TotalUsers.w_val ? s.TotalUsers.w_val : s.TotalUsers.min} max={s.TotalUsers.max} id="TotalUsers_1" key="TotalUsers_1" value={s.TotalUsers.c_val} onChange={this.onChange} /></td>
                            <td><input type='number' min={s.TotalUsers.min_size} max={s.TotalUsers.max_size} id="TotalUsers_2" key="TotalUsers_2" value={s.TotalUsers.size} onChange={this.onChange} /></td>
                        </tr>
                    </table>
                    <input type="submit" className="btn btn-primary" value="Apply changes" />
                </form>
            </div>
        );
    }
});

Triggers = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Triggers);

module.exports = Triggers;

